import pika
import json

RABBITMQ_HOST = 'localhost'

def publish_new_message_event(group_id: int, message_id: int, sender_id: int):
    """
    Publica un evento en RabbitMQ para que otros servicios 
    (como Grupos o Notificaciones) lo procesen en segundo plano.
    """
    try:
        # 1. Establecer conexión con el servidor RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        # 2. Declarar la "cola" (si no existe, RabbitMQ la crea)
        queue_name = 'nuevos_mensajes_queue'
        channel.queue_declare(queue=queue_name, durable=True)

        # 3. Preparar el mensaje (payload) en formato JSON
        evento = {
            "action": "generar_recibos",
            "group_id": group_id,
            "message_id": message_id,
            "sender_id": sender_id
        }

        # 4. Enviar el mensaje a la cola
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(evento),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE # El mensaje no se borra si RabbitMQ se reinicia
            )
        )
        print(f"🐇 [RabbitMQ] Evento asíncrono publicado: {evento}")
        
        # 5. Cerrar la conexión
        connection.close()
    except Exception as e:
        print(f"❌ [RabbitMQ] Error de conexión: {e}")