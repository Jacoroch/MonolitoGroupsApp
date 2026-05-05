import pika
import json
import os
import sys

# --- CONFIGURACIÓN DE RUTAS (LA MAGIA PARA EL MONOREPO) ---
# Como estamos en modules/consumers/messaging_worker.py (2 niveles de profundidad),
# usamos os.path para subir 2 niveles hasta la raíz de gruops-app_Micro/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.database import SessionLocal
from modules.messaging import models as msg_models

# Importamos Group temporalmente usando nuestra estrategia de BD compartida
from modules.groups.models import Group

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

def callback(ch, method, properties, body):
    """Esta función se ejecuta automáticamente cuando llega un mensaje a la cola"""
    data = json.loads(body)
    message_id = data.get("message_id")
    group_id = data.get("group_id")
    sender_id = data.get("sender_id")

    print(f"\n📩 [WORKER MENSAJERÍA] Evento recibido | Msg ID: {message_id} | Grupo: {group_id}")
    
    db = SessionLocal()
    try:
        # 1. Buscamos el grupo para saber quiénes son sus miembros actuales
        group = db.query(Group).filter(Group.id == group_id).first()
        
        if not group:
            print(f"⚠️ [WORKER] El grupo {group_id} no existe. Ignorando evento.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"⚙️  [WORKER] Generando recibos para los miembros del grupo...")
        
        # 2. Creamos los recibos de lectura para todos excepto el que envió el mensaje
        recibos_creados = 0
        for member in group.members:
            if member.id != sender_id:
                nuevo_recibo = msg_models.MessageReceipt(
                    message_id=message_id,
                    user_id=member.id
                    # read_at se maneja como nulo por defecto en la base de datos
                )
                db.add(nuevo_recibo)
                recibos_creados += 1
                
        # 3. Guardamos todos los recibos en bloque en la base de datos
        db.commit()
        
        print(f"✅ [WORKER] {recibos_creados} recibos creados exitosamente en la BD.")
        
        # 4. Confirmamos a RabbitMQ que el trabajo se completó con éxito (Acknowledge)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ [WORKER] Error crítico procesando el mensaje {message_id}: {e}")
        db.rollback() # Cancelamos cualquier cambio a medias en la base de datos
        # Devolvemos el mensaje a la cola para que no se pierda y se intente de nuevo
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()

def start_worker():
    """Configura la conexión a RabbitMQ y empieza a escuchar"""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        # Aseguramos que la cola existe
        channel.queue_declare(queue='nuevos_mensajes_queue', durable=True)
        
        # Balanceo de carga: solo dar 1 mensaje a la vez a este worker
        channel.basic_qos(prefetch_count=1)
        
        # Asignamos la función callback a la cola
        channel.basic_consume(queue='nuevos_mensajes_queue', on_message_callback=callback)

        print('🚀 [WORKER MENSAJERÍA] Corriendo y escuchando en la cola de RabbitMQ... (CTRL+C para salir)')
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("❌ [WORKER] No se pudo conectar a RabbitMQ. ¿Está corriendo tu contenedor de Docker?")
    except Exception as e:
        print(f"❌ [WORKER] Error inesperado: {e}")

if __name__ == '__main__':
    try:
        start_worker()
    except KeyboardInterrupt:
        print('\n🛑 Worker detenido por el usuario.')
        sys.exit(0)