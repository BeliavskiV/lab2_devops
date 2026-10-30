import json
import os
import time
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC_NAME = "test_stream_topic"

def main():
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    for i in range(1, 11):
        event = {"id": i, "message": f"Kafka stream message #{i}", "timestamp": time.time()}
        producer.send(TOPIC_NAME, value=event)
        producer.flush()
        print(f"[Kafka Producer] Sent: {event}", flush=True)
        time.sleep(2)

if __name__ == "__main__":
    main()
