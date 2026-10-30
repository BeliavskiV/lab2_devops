import os
import time
import pika

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_NAME = "app_events"
LOG_FILE = "/var/data/produced_messages.log"

def main():
    os.makedirs("/var/data", exist_ok=True)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    for i in range(1, 6):
        msg = f"Event #{i} payload"
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"SENT: {msg}\n")
        print(f"[Producer] Sent: {msg}", flush=True)
        time.sleep(2)

    connection.close()

if __name__ == "__main__":
    main()
