import os, json, pika

BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@rabbitmq:5672/")
QUEUE_NAME = os.getenv("QUEUE_NAME", "calc.success")

def publish_success_event(evt: dict):
    params = pika.URLParameters(BROKER_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)
    ch.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(evt).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    conn.close()
