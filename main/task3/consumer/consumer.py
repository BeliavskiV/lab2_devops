import json
import os
from kafka import KafkaConsumer

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC_NAME = "test_stream_topic"

def main():
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="lab2_consumer_group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )
    print("[Kafka Consumer] Listening for messages...", flush=True)
    for msg in consumer:
        print(f"[Kafka Consumer] Partition: {msg.partition}, Offset: {msg.offset}, Value: {msg.value}", flush=True)

if __name__ == "__main__":
    main()
