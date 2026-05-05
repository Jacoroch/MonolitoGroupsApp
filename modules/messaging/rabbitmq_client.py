import pika
import json
import os

# 1. Leemos la variable de entorno. Si el Gateway no la encuentra, usará 'localhost' (lo cual fallará en Docker)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

def publish_new_message_event(group_id: int, message_id: int, sender_id: int):
    print(f"\n🐇 [RabbitMQ Gateway] Intentando enviar evento. Destino: {RABBITMQ_HOST}...")
    
    try:
        # 2. Establecemos la conexión
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        
        # 3. Garantizamos que la cola exista antes de lanzar el mensaje
        channel.queue_declare(queue='nuevos_mensajes_queue', durable=True)
        
        # 4. Preparamos los datos
        mensaje_data = {
            "group_id": group_id,
            "message_id": message_id,
            "sender_id": sender_id
        }
        
        # 5. Publicamos el mensaje en la cola
        channel.basic_publish(
            exchange='',
            routing_key='nuevos_mensajes_queue',
            body=json.dumps(mensaje_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hace que el mensaje sea persistente (no se borra si RabbitMQ se reinicia)
            )
        )
        
        print(f"✅ [RabbitMQ Gateway] Evento encolado con éxito. Msg ID: {message_id}")
        connection.close()
        
    except Exception as e:
        # Aquí capturaremos el error REAL de la librería pika
        print(f"❌ [RabbitMQ Gateway] Fallo al conectar o publicar: {type(e).__name__} - {str(e)}")