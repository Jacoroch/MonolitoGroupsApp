import pika
import json
import os
import sys
import grpc

# Rutas para el monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# ✅ IMPORTAMOS SOLO LA BASE DE DATOS DE MENSAJES
from core.database import SessionLocalMessages
from modules.messaging import models as msg_models

# ✅ IMPORTAMOS LOS CONTRATOS gRPC DE GRUPOS
from protos import groups_pb2, groups_pb2_grpc

# ✅ IMPORTAMOS CONSUL
from core.consul_registry import get_service_url

# RabbitMQ es infraestructura (no cambia de IP a cada rato), así que se queda igual
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
# Mantenemos esto solo como "plan de respaldo"
FALLBACK_GROUPS_URL = os.getenv('GROUPS_SERVER_URL', 'groups-grpc-server:50052')

def get_group_members(group_id: int):
    """Llama al microservicio de Grupos por gRPC para obtener los IDs de los miembros"""
    
    # ✅ LE PREGUNTAMOS A CONSUL DÓNDE ESTÁ GRUPOS
    groups_url = get_service_url("groups-service", FALLBACK_GROUPS_URL)
    print(f"📞 [WORKER] Consultando miembros del grupo {group_id} vía gRPC en {groups_url}...")
    
    try:
        with grpc.insecure_channel(groups_url) as channel:
            stub = groups_pb2_grpc.GroupServiceStub(channel)
            request = groups_pb2.GroupRequest(group_id=group_id)
            response = stub.GetGroupMembers(request)
            return list(response.user_ids)
    except Exception as e:
        print(f"❌ [WORKER] Error conectando a Grupos por gRPC: {e}")
        return []

def callback(ch, method, properties, body):
    """Esta función se ejecuta automáticamente cuando llega un mensaje a la cola"""
    data = json.loads(body)
    message_id = data.get("message_id")
    group_id = data.get("group_id")
    sender_id = data.get("sender_id")

    print(f"\n📩 [WORKER] Evento recibido | Msg ID: {message_id} | Grupo: {group_id}")
    
    # 1. Obtener miembros vía gRPC (¡Cero cruce de bases de datos!)
    member_ids = get_group_members(group_id)
    
    if not member_ids:
        print(f"⚠️ [WORKER] El grupo {group_id} no tiene miembros o hubo un error.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    print(f"⚙️  [WORKER] Generando recibos para {len(member_ids)} miembros...")
    
    # 2. Nos conectamos EXCLUSIVAMENTE a la base de datos de mensajes
    db = SessionLocalMessages()
    try:
        recibos_creados = 0
        for user_id in member_ids:
            if user_id != sender_id:
                nuevo_recibo = msg_models.MessageReceipt(
                    message_id=message_id,
                    user_id=user_id
                )
                db.add(nuevo_recibo)
                recibos_creados += 1
                
        db.commit()
        print(f"✅ [WORKER] {recibos_creados} recibos creados exitosamente en messages_db.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ [WORKER] Error crítico procesando el mensaje {message_id}: {e}")
        db.rollback() 
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()

def start_worker():
    """Configura la conexión a RabbitMQ y empieza a escuchar"""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        channel.queue_declare(queue='nuevos_mensajes_queue', durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='nuevos_mensajes_queue', on_message_callback=callback)

        print('🚀 [WORKER MENSAJERÍA] Corriendo y escuchando en la cola de RabbitMQ...')
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError:
        print("❌ [WORKER] No se pudo conectar a RabbitMQ.")
    except Exception as e:
        print(f"❌ [WORKER] Error inesperado: {e}")

if __name__ == '__main__':
    try:
        start_worker()
    except KeyboardInterrupt:
        print('\n🛑 Worker detenido por el usuario.')
        sys.exit(0)