import os
import pika

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_NAME = "app_events"
OUT_FILE = "/var/data/consumed_messages.log"

def main():
    os.makedirs("/var/data", exist_ok=True)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    def callback(ch, method, properties, body):
        msg = body.decode()
        print(f"[Consumer] Received: {msg}", flush=True)
        with open(OUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"RECEIVED: {msg}\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print("[Consumer] Waiting for messages...", flush=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()
