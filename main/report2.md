# БЕЛОРУССКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ
**Факультет прикладной математики и информатики**  
**Кафедра технологий программирования**

## Отчет по лабораторной работе №2
**Тема:** Коммуникация в многоконтейнерных системах  
**Дисциплина:** «Непрерывное интегрирование и сборка программного обеспечения»  

**Выполнил:** студент 11 группы Белявский Владислав Алексеевич  
**Вариант:** 1  
**Преподаватель:** ст. преподаватель Давидовская М. И.  

Минск, 2026 г.

---

## 1. Цель и задачи работы

**Цель работы:**  
Проектирование распределенных систем и реализация коммуникации между их компонентами.

**Задачи работы:**
1. Реализовать простую распределенную систему с использованием связанных томов монтирования (`bind mounts`).
2. Реализовать распределенную систему с асинхронным обменом на основе брокера сообщений RabbitMQ.
3. Реализовать распределенную систему с асинхронным обменом на основе потоковой системы Apache Kafka (режим KRaft + AKHQ).
4. Оформить отчёт в формате Markdown и опубликовать результаты в Git-репозитории.

---

## 2. Вариант задания (Вариант №1)

Согласно варианту №1 для Задания 1 необходимо разработать два взаимодействующих контейнеризированных приложения, работающих с текстовыми файлами, содержащими целые числа:

| № варианта | Программа 1 (`worker1`) | Программа 2 (`worker2`) |
| :--- | :--- | :--- |
| **1** | Ищет в каталоге `/var/data` самый большой по объёму файл и перекладывает его в `/var/result/data.txt`. | Сохраняет произведение первого и последнего числа из файла `/var/data/data.txt` в `/var/result/result.txt` и дополнительно выводит результат на экран. |

Схема монтирования каталогов относительно каталога `task1`:
* `./data` $\rightarrow$ `/var/data` для `worker1` (исходные данные).
* `./result-1` $\rightarrow$ `/var/result` для `worker1` (промежуточные данные).
* `./result-1` $\rightarrow$ `/var/data` для `worker2` (входные данные для второй программы).
* `./result` $\rightarrow$ `/var/result` для `worker2` (финальные результаты).

---

## 3. Задание 1. Разработка простейшего распределенного приложения

### 3.1. Структура каталога `task1`
```text
task1/
├── compose.yaml
├── .gitignore
├── .dockerignore
├── Readme.md
├── data/
│   ├── small.txt
│   └── large.txt
├── result-1/
│   └── data.txt
├── result/
│   └── result.txt
├── worker1/
│   ├── app.py
│   └── Dockerfile
└── worker2/
    ├── app.py
    └── Dockerfile
```

### 3.2. Исходный код и конфигурационные файлы

#### Программа 1 (`task1/worker1/app.py`)
```python
import os
import shutil
import sys

DATA_DIR = "/var/data"
RESULT_DIR = "/var/result"
OUTPUT_FILE = os.path.join(RESULT_DIR, "data.txt")

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Каталог {DATA_DIR} не найден.")
        sys.exit(1)

    files = [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if os.path.isfile(os.path.join(DATA_DIR, f))
    ]

    if not files:
        print("В каталоге /var/data нет файлов.")
        sys.exit(1)

    # Поиск самого большого по объему файла
    largest_file = max(files, key=os.path.getsize)
    os.makedirs(RESULT_DIR, exist_ok=True)
    shutil.copyfile(largest_file, OUTPUT_FILE)
    print(f"Worker 1: Самый большой файл '{os.path.basename(largest_file)}' скопирован в {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
```

#### Конфигурация `task1/worker1/Dockerfile`
```dockerfile
# Базовый легковесный образ Python
FROM python:3.11-slim

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копирование исходного кода программы 1 в контейнер
COPY app.py .

# Создание точек монтирования для входных и выходных данных
VOLUME ["/var/data", "/var/result"]

# Команда запуска приложения при старте контейнера
CMD ["python", "app.py"]
```

#### Программа 2 (`task1/worker2/app.py`)
```python
import os
import sys

INPUT_FILE = "/var/data/data.txt"
RESULT_DIR = "/var/result"
OUTPUT_FILE = os.path.join(RESULT_DIR, "result.txt")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        numbers = [int(token) for token in f.read().split()]

    if not numbers:
        print("Файл пуст или не содержит чисел.")
        sys.exit(1)

    product = numbers[0] * numbers[-1]

    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"{product}\n")

    print(f"Первое число: {numbers[0]}, Последнее число: {numbers[-1]}")
    print(f"Результат (произведение): {product}")

if __name__ == "__main__":
    main()
```

#### Конфигурация `task1/worker2/Dockerfile`
```dockerfile
# Базовый легковесный образ Python
FROM python:3.11-slim

# Установка рабочей директории внутри контейнера
WORKDIR /app

# Копирование исходного кода программы 2 в контейнер
COPY app.py .

# Создание точек монтирования для промежуточных и финальных данных
VOLUME ["/var/data", "/var/result"]

# Команда запуска приложения при старте контейнера
CMD ["python", "app.py"]
```

#### Файл оркестрации `task1/compose.yaml`
```yaml
services:
  worker1:
    build: ./worker1
    container_name: task1_worker1
    volumes:
      - ./data:/var/data
      - ./result-1:/var/result

  worker2:
    build: ./worker2
    container_name: task1_worker2
    volumes:
      - ./result-1:/var/data
      - ./result:/var/result
    depends_on:
      worker1:
        condition: service_completed_successfully
```

#### Файлы `.gitignore` и `.dockerignore`
```text
__pycache__/
*.pyc
.env
result-1/*
result/*
!result-1/.gitkeep
!result/.gitkeep
```

### 3.3. Результаты тестирования Задания 1
Входные файлы в каталоге `data/`:
* `data/small.txt`: `10`, `20`, `30` (размер 9 байт).
* `data/large.txt`: `5`, `12`, `45`, `100`, `8`, `25` (размер 19 байт).

Запуск и вывод в терминале:
```text
user@WIN-RF157T1A1N2:~/lab2/main/task1$ docker compose up --build
[+] Running 2/2
 ✔ Container task1_worker1  Created
 ✔ Container task1_worker2  Created
Attaching to task1_worker1, task1_worker2
task1_worker1  | Worker 1: Самый большой файл 'large.txt' скопирован в /var/result/data.txt
task1_worker1 exited with code 0
task1_worker2  | Первое число: 5, Последнее число: 25
task1_worker2  | Результат (произведение): 125
task1_worker2 exited with code 0

user@WIN-RF157T1A1N2:~/lab2/main/task1$ cat result/result.txt
125
```

---

## 4. Задание 2. Асинхронная коммуникация на основе брокера сообщений RabbitMQ

### 4.1. Упражнение 2.1 (Работа с обменниками, очередями и JSON-сообщениями)
В рамках упражнения настроена точка обмена `orders_exchange` типа `direct`, создана очередь `orders_queue` и привязка (`Binding`) с ключом маршрутизации `order.new`.

Файл `task2-1/payload.json`:
```json
{
  "order_id": 101,
  "customer": "Vladislav Belyavsky",
  "items": [
    {"product_id": 1, "name": "Keyboard", "price": 150}
  ],
  "status": "NEW"
}
```

### 4.2. Упражнение 2.2 (Настройка RabbitMQ в Docker и прохождение Tutorials 1–3)

#### Файл `task2-2/compose.yaml`
```yaml
services:
  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    container_name: rabbitmq_task2_2
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
```

#### Урок 1: Hello World (`tut1_send.py` и `tut1_receive.py`)
```python
# tut1_send.py
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')
channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
print(" [x] Sent 'Hello World!'")
connection.close()
```

```python
# tut1_receive.py
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='hello')

def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")

channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
```

#### Урок 2: Work Queues (`tut1_task.py` и `tut2_worker.py`)
```python
# tut1_task.py
import sys
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

message = ' '.join(sys.argv[1:]) or "Hello Work Queue..."
channel.basic_publish(
    exchange='',
    routing_key='task_queue',
    body=message,
    properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
)
print(f" [x] Sent {message}")
connection.close()
```

```python
# tut2_worker.py
import time
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='task_queue', durable=True)

def callback(ch, method, properties, body):
    text = body.decode()
    print(f" [x] Received {text}")
    time.sleep(text.count('.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)
print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
```

#### Урок 3: Publish/Subscribe (`tut3_emit_logs.py` и `tut3_receive_logs.py`)
```python
# tut3_emit_logs.py
import sys
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='logs', exchange_type='fanout')

message = ' '.join(sys.argv[1:]) or "info: Hello World!"
channel.basic_publish(exchange='logs', routing_key='', body=message)
print(f" [x] Sent {message}")
connection.close()
```

```python
# tut3_receive_logs.py
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='logs', exchange_type='fanout')

result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='logs', queue=queue_name)

def callback(ch, method, properties, body):
    print(f" [x] {body.decode()}")

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
print(' [*] Waiting for logs. To exit press CTRL+C')
channel.start_consuming()
```

### 4.3. Упражнение 2.3 (Распределенная система в контейнерах + Bind Mounts + ИИ-агент + CLI-утилиты)

#### Код издателя (`task2-3/producer/producer.py`)
```python
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
```

#### `task2-3/producer/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pika
COPY producer.py .
CMD ["python", "producer.py"]
```

#### Код потребителя (`task2-3/consumer/consumer.py`)
```python
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
```

#### `task2-3/consumer/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pika
COPY consumer.py .
CMD ["python", "consumer.py"]
```

#### Конфигурация `task2-3/compose.yaml`
```yaml
services:
  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    container_name: task2_3_rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  producer:
    build: ./producer
    container_name: task2_3_producer
    environment:
      RABBIT_HOST: rabbitmq
    volumes:
      - ./data/producer:/var/data
    depends_on:
      rabbitmq:
        condition: service_healthy

  consumer:
    build: ./consumer
    container_name: task2_3_consumer
    environment:
      RABBIT_HOST: rabbitmq
    volumes:
      - ./data/consumer:/var/data
    depends_on:
      rabbitmq:
        condition: service_healthy

  ollama:
    image: ollama/ollama:latest
    container_name: task2_3_ai_agent
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

#### Протокол выполнения и демонстрация консольных утилит (`rabbitmqctl` и `rabbitmqadmin`)

Ниже представлены реальные запросы и ответы консоли при сборке образов и проверке состояния брокера:

**1. Сборка контейнеров `task2-3`:**
```text
user@WIN-RF157T1A1N2:~/lab2/main$ mkdir -p task2-3/{producer,consumer,data/producer,data/consumer}
user@WIN-RF157T1A1N2:~/lab2/main$ cd task2-3
user@WIN-RF157T1A1N2:~/lab2/main/task2-3$ docker compose up -d
[+] Building 5.6s (17/17) FINISHED
 => [producer internal] load build definition from Dockerfile                                   0.0s
 => [consumer internal] load build definition from Dockerfile                                   0.1s
 => [consumer internal] load metadata for docker.io/library/python:3.11-slim                    1.2s
 => [producer 1/4] FROM docker.io/library/python:3.11-slim@sha256:673719e071ecf...              0.1s
 => CACHED [producer 2/4] WORKDIR /app                                                          0.0s
 => [producer 3/4] RUN pip install --no-cache-dir pika                                          2.9s
 => [producer 4/4] COPY producer.py .                                                           0.1s
 => [consumer 4/4] COPY consumer.py .                                                           0.1s
 => [producer] exporting to image                                                               0.9s
 => => naming to docker.io/library/task2-3-producer:latest                                      0.0s
 => [consumer] exporting to image                                                               0.9s
 => => naming to docker.io/library/task2-3-consumer:latest                                      0.0s
[+] up 4/4
 ✔ Image task2-3-producer      Built                                                            5.8s
 ✔ Image task2-3-consumer      Built                                                            5.8s
 ✔ Network task2-3_default     Created                                                          0.0s
 ✔ Volume task2-3_ollama_data  Created                                                          0.0s
 ✔ Container task2_3_rabbitmq  Healthy                                                          6.2s
 ✔ Container task2_3_ai_agent  Started                                                          0.6s
 ✔ Container task2_3_producer  Started                                                          0.2s
 ✔ Container task2_3_consumer  Started                                                          0.2s
```

**2. Запрос списка точек обмена и очередей через `rabbitmqadmin`:**
```text
user@WIN-RF157T1A1N2:~/lab2/main/task2-3$ docker exec task2_3_rabbitmq rabbitmqadmin list exchanges
+--------------------+---------+
|        name        |  type   |
+--------------------+---------+
|                    | direct  |
| amq.direct         | direct  |
| amq.fanout         | fanout  |
| amq.headers        | headers |
| amq.match          | headers |
| amq.rabbitmq.trace | topic   |
| amq.topic          | topic   |
+--------------------+---------+
user@WIN-RF157T1A1N2:~/lab2/main/task2-3$ docker exec task2_3_rabbitmq rabbitmqadmin list queues
No items
```

**3. Диагностика состояния узла через `rabbitmqctl status`:**
```text
user@WIN-RF157T1A1N2:~/lab2/main/task2-3$ docker exec task2_3_rabbitmq rabbitmqctl status
Status of node rabbit@07e323de37f2 ...
Runtime

OS PID: 1
OS: Linux
Uptime (seconds): 56
Is under maintenance?: false
RabbitMQ version: 3.13.7
RabbitMQ release series support status: see https://www.rabbitmq.com/release-information
Node name: rabbit@07e323de37f2
Erlang configuration: Erlang/OTP 26 [erts-14.2.5.12] [source] [64-bit] [smp:32:32] [ds:32:32:10] [async-threads:1] [jit]
Crypto library: OpenSSL 3.1.8 11 Feb 2025
Erlang processes: 493 used, 1048576 limit
Scheduler run queue: 1
Cluster heartbeat timeout (net_ticktime): 60

Plugins

Enabled plugin file: /etc/rabbitmq/enabled_plugins
Enabled plugins:

 * rabbitmq_prometheus
 * rabbitmq_federation
 * accept
 * prometheus
 * rabbitmq_management
 * rabbitmq_management_agent
 * rabbitmq_web_dispatch
 * amqp_client
 * cowboy
 * cowlib
 * oauth2_client
 * jose

Data directory

Node data directory: /var/lib/rabbitmq/mnesia/rabbit@07e323de37f2
Raft data directory: /var/lib/rabbitmq/mnesia/rabbit@07e323de37f2/quorum/rabbit@07e323de37f2

Config files

 * /etc/rabbitmq/conf.d/10-defaults.conf

Log file(s)

 * <stdout>

Alarms

(none)

Memory

Total memory used: 0.1932 gb
Calculation strategy: rss
Memory high watermark setting: 0.4 of available memory, computed to: 3.1624 gb

File Descriptors

Total: 0, limit: 1048479
Sockets: 0, limit: 943629

Free Disk Space

Low free disk space watermark: 0.05 gb
Free disk space: 1013.8406 gb

Totals

Connection count: 0
Queue count: 0
Virtual host count: 1

Listeners

Interface: [::], port: 15672, protocol: http, purpose: HTTP API
Interface: [::], port: 15692, protocol: http/prometheus, purpose: Prometheus exporter API over HTTP
Interface: [::], port: 25672, protocol: clustering, purpose: inter-node and CLI tool communication
Interface: [::], port: 5672, protocol: amqp, purpose: AMQP 0-9-1 and AMQP 1.0
```

---

## 5. Задание 3. Асинхронная коммуникация на основе потоковой системы Apache Kafka

### 5.1. Исходный код и конфигурационные файлы (`task3`)

#### Издатель (`task3/producer/producer.py`)
```python
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
```

#### `task3/producer/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python-ng
COPY producer.py .
CMD ["python", "producer.py"]
```

#### Потребитель (`task3/consumer/consumer.py`)
```python
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
```

#### `task3/consumer/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python-ng
COPY consumer.py .
CMD ["python", "consumer.py"]
```

#### Конфигурация `task3/compose.yaml` (Kafka KRaft + AKHQ + Producer + Consumer)
```yaml
services:
  kafka:
    image: confluentinc/cp-kafka:7.6.0
    container_name: kafka_local
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092'
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:29093'
      KAFKA_LISTENERS: 'PLAINTEXT://0.0.0.0:29092,CONTROLLER://0.0.0.0:29093,PLAINTEXT_HOST://0.0.0.0:9092'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_LOG_DIRS: '/tmp/kraft-combined-logs'
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server kafka:29092"]
      interval: 10s
      timeout: 5s
      retries: 5

  akhq:
    image: tchiotludo/akhq:latest
    container_name: akhq_local
    ports:
      - "8080:8080"
    environment:
      AKHQ_CONFIGURATION: |
        akhq:
          connections:
            docker-kafka-cluster:
              properties:
                bootstrap.servers: "kafka:29092"
    depends_on:
      kafka:
        condition: service_healthy

  producer:
    build: ./producer
    container_name: kafka_producer
    environment:
      BOOTSTRAP_SERVERS: "kafka:29092"
    depends_on:
      kafka:
        condition: service_healthy

  consumer:
    build: ./consumer
    container_name: kafka_consumer
    environment:
      BOOTSTRAP_SERVERS: "kafka:29092"
    depends_on:
      kafka:
        condition: service_healthy
```

---

## 6. Ответы на контрольные вопросы

**1. Что такое обмен сообщениями (messaging) и какие проблемы в архитектуре ПО он решает?**  
Обмен сообщениями — это метод асинхронной межпроцессной коммуникации, при котором программные компоненты взаимодействуют друг с другом путём отправки и получения дискретных пакетов данных (сообщений) через посредника. Он решает проблемы жёсткой связанности компонентов (tight coupling), сглаживает пиковые нагрузки (буферизация), повышает отказоустойчивость (сообщения не теряются, если получатель временно недоступен) и упрощает горизонтальное масштабирование.

**2. Что такое брокер сообщений? Какова его роль в системе?**  
Брокер сообщений — это промежуточное программное обеспечение (middleware), выступающее посредником между отправителями (producers) и получателями (consumers). Его роль заключается в приёме сообщений, их валидации, маршрутизации по заданным правилам, временном или долговременном хранении в очередях/топиках и гарантированной доставке подписчикам.

**3. Перечислите и охарактеризуйте основные шаблоны (паттерны) обмена сообщениями.**  
* **Point-to-Point (Точка-точка / Очередь задач):** сообщение отправляется в очередь и обрабатывается ровно одним из подключенных к ней потребителей.
* **Publish/Subscribe (Издатель-Подписчик):** сообщение публикуется в тему/обменник, и его копию получают все активные подписчики.
* **Request/Reply (Запрос-Ответ / RPC поверх очередей):** отправитель посылает сообщение-запрос, указывая обратную очередь (`reply_to`) и идентификатор корреляции (`correlation_id`), и ожидает ответа.

**4. Дайте определение RabbitMQ.**  
RabbitMQ — это распределённый брокер сообщений с открытым исходным кодом, написанный на языке Erlang и реализующий концепцию «умного брокера» с гибкой маршрутизацией сообщений и управлением очередями.

**5. Какой протокол лежит в основе RabbitMQ?**  
В основе RabbitMQ лежит протокол **AMQP 0-9-1** (Advanced Message Queuing Protocol). Дополнительно с помощью плагинов поддерживаются протоколы AMQP 1.0, MQTT, STOMP и WebSockets.

**6. В RabbitMQ сообщения, принятые от приложения-продюсера (издателя), записываются...**  
После прохождения через точку обмена (Exchange) и срабатывания правил маршрутизации сообщения записываются и хранятся в **очередях (Queues)**.

**7. Объясните, что такое точка обмена (exchange).**  
Точка обмена (Exchange) — это входной маршрутизатор внутри RabbitMQ, который принимает сообщения от продюсеров и определяет, в какие очереди (или другие обменники) следует направить копии сообщения в соответствии с типом обменника, ключом маршрутизации и привязками (bindings).

**8. Что такое Binding в RabbitMQ?**  
Binding (привязка) — это связующее правило между точкой обмена (Exchange) и очередью (Queue), указывающее брокеру, при каких условиях (например, при каком значении `Routing Key` или заголовков) сообщение из данного обменника должно попасть в данную очередь.

**9. Дайте определение Routing Key в RabbitMQ.**  
Routing Key (ключ маршрутизации) — это строковый атрибут в метаданных публикуемого сообщения, который точка обмена проверяет при сопоставлении с ключами привязок (`Binding Keys`) для выбора целевых очередей.

**10. Опишите по шагам процесс маршрутизации сообщения в RabbitMQ (от продюсера до потребителя).**  
1. Продюсер устанавливает TCP-соединение и открывает виртуальный канал (Channel) с брокером.  
2. Продюсер публикует сообщение в указанную точку обмена (`Exchange`), снабжая его ключом маршрутизации (`Routing Key`).  
3. `Exchange` анализирует свой тип, `Routing Key` (или заголовки) и таблицу привязок (`Bindings`).  
4. Сообщение помещается в одну или несколько подходящих очередей (`Queues`).  
5. Брокер доставляет (по модели Push) сообщение подписанному на очередь потребителю (`Consumer`).  
6. Потребитель обрабатывает данные и отправляет брокеру подтверждение (`basic_ack`).  
7. Получив `ack`, RabbitMQ окончательно удаляет сообщение из очереди.

**11. Если необходимо просто распараллелить обработку сообщений, принятых от продюсера (издателя) по нескольким потребителям, какой тип обменника надо выбрать в RabbitMQ?**  
Если требуется распределить поток задач между несколькими воркерами по принципу Round-Robin (каждое сообщение обрабатывается только одним свободным воркером), выбирается обменник типа **`direct`** (или обменник по умолчанию `""`), направляющий сообщения в одну общую очередь с несколькими консьюмерами. Если же нужно параллельно отправить копию одного сообщения разным независимым обработчикам одновременно — выбирается тип **`fanout`**.

**12. Какие типы точек обмена (exchanges) существуют в RabbitMQ и в чем их принципиальные отличия?**  
* **`direct`** — направляет сообщение в очереди, чей `binding key` в точности совпадает с `routing key` сообщения.
* **`fanout`** — безусловно рассылает копии сообщения во все привязанные к нему очереди (игнорирует `routing key`).
* **`topic`** — маршрутизирует сообщения по маске/шаблону в `routing key` (слова, разделенные точками, с подстановочными знаками `*` — ровно одно слово и `#` — ноль или более слов).
* **`headers`** — маршрутизирует сообщения на основе совпадения атрибутов в заголовках (`Headers`), игнорируя `routing key` (с параметром `x-match: all` или `any`).

**13. Обычно приложение-продюсер, отправляя сообщение в RabbitMQ, отправляет его...**  
В **точку обмена (Exchange)**. Продюсер в RabbitMQ никогда не публикует сообщения напрямую в очередь (даже при отправке в очередь по имени используется безымянный дефолтный обменник `""`).

**14. Как предотвратить потребление устаревших данных из RabbitMQ?**  
С помощью механизма **TTL (Time-To-Live — время жизни)**. Его можно задать на уровне всей очереди при её объявлении (аргумент `x-message-ttl`) или на уровне конкретного сообщения при публикации (свойство `expiration`). По истечении TTL непрочитанное сообщение автоматически удаляется или перенаправляется в Dead Letter Exchange.

**15. По какому принципу LIFO или FIFO устроены очереди в RabbitMQ, в которые записываются сообщения?**  
Очереди в RabbitMQ работают строго по принципу **FIFO** (*First-In, First-Out* — «первым пришёл — первым обслужен»), за исключением случаев использования приоритетных очередей или повторной постановки в очередь (`requeue`).

**16. Для чего предназначен Server (Broker/Node) в RabbitMQ?**  
Узел (Server/Broker) — это запущенный экземпляр виртуальной машины Erlang с приложением RabbitMQ, который управляет сетевыми подключениями, каналами, виртуальными хостами, обменниками, очередями, дисковым хранилищем Mnesia и маршрутизацией.

**17. Опишите назначение Virtual Host (Vhost) в RabbitMQ.**  
Virtual Host (виртуальный хост) обеспечивает логическую изоляцию (мультитенантность) внутри одного брокера RabbitMQ. Каждый `vhost` имеет собственные независимые точки обмена, очереди, привязки и права доступа пользователей, что позволяет безопасно разделять разные проекты или среды (`dev`, `stage`, `prod`) на одном физическом сервере.

**18. Что такое подтверждение сообщений (acknowledgments / ack, nack, reject) и зачем оно необходимо?**  
Это механизм обратной связи от потребителя к брокеру (Consumer Acknowledgements), гарантирующий надёжную доставку (at-least-once):
* **`basic.ack`** — положительное подтверждение: сообщение успешно обработано, брокер может удалить его.
* **`basic.reject`** — отрицательное подтверждение для одного сообщения (позволяет либо вернуть его в очередь `requeue=true`, либо сбросить/отправить в DLX `requeue=false`).
* **`basic.nack`** — расширенный аналог `reject`, поддерживающий пакетное отклонение нескольких сообщений сразу (`multiple=true`).

**19. Чем отличаются долговечные (durable) и временные (transient) очереди и сообщения? Как это влияет на перезагрузку брокера?**  
* **Durable очередь** сохраняет свои метаданные на диск и восстанавливается после перезапуска брокера; **Transient очередь** удаляется при рестарте узла.
* **Persistent сообщение** (`delivery_mode=2`) записывается на диск; **Transient сообщение** (`delivery_mode=1`) хранится в оперативной памяти.  
Чтобы сообщение гарантированно пережило перезагрузку брокера, **и очередь должна быть `durable`, и само сообщение должно быть опубликовано как `persistent`**.

**20. Что такое Dead Letter Exchange (DLX) и какие сценарии его использования?**  
Dead Letter Exchange (DLX) — это обычная точка обмена, привязанная к очереди через аргумент `x-dead-letter-exchange`, куда автоматически перенаправляются «мёртвые» сообщения в трёх случаях:
1. Потребитель отклонил сообщение (`basic.reject` / `basic.nack`) с параметром `requeue=false`.
2. Истекло время жизни сообщения (TTL).
3. Превышен лимит длины очереди (`x-max-length`).  
*Сценарии использования:* изолированный разбор сбоев (логирование проблемных сообщений), реализация отложенных очередей (delayed retries через связку TTL + DLX).

**21. Что такое Priority Queue в RabbitMQ и как она работает?**  
Приоритетная очередь — это очередь, созданная с аргументом `x-max-priority` (обычно от 1 до 10). При публикации сообщения продюсер указывает его приоритет в свойстве `priority`. Брокер помещает сообщения с более высоким приоритетом в начало очереди перед сообщениями с меньшим приоритетом.

**22. Дайте определение Apache Kafka. Какие основные задачи она решает и чем ее философия отличается от классических брокеров?**  
Apache Kafka — это распределённая, горизонтально масштабируемая платформа потоковой передачи событий (distributed event streaming platform).  
*Отличие философии:* классические брокеры (RabbitMQ) строятся вокруг принципа «умный брокер / простые консьюмеры» и удаляют сообщение сразу после его обработки. Kafka строится вокруг неизменяемого распределённого журнала коммитов (append-only commit log) и принципа «простой брокер / умные консьюмеры»: сообщения сохраняются на диске в течение заданного периода (retention) независимо от того, сколько раз их прочитали, а позицию чтения (`offset`) отслеживает сам потребитель.

**23. Опишите архитектуру Kafka. Что такое Broker, Topic и Partition?**  
* **Broker** — отдельный сервер Kafka в кластере, хранящий данные на диске и обслуживающий запросы клиентов.
* **Topic (Топик)** — логическая категория или именованный поток, в который публикуются записи.
* **Partition (Партиция / Раздел)** — физическая единица хранения и параллелизма. Каждый топик разбивается на одну или несколько партиций. Партиция представляет собой упорядоченный неизменяемый лог-файл, где каждому сообщению присваивается последовательный номер — смещение (`offset`). Порядок сообщений гарантируется только внутри одной партиции.

**24. Что такое Consumer Group (группа потребителей) и как она влияет на масштабирование и распараллеливание чтения?**  
Consumer Group — это набор экземпляров приложений-потребителей с одинаковым `group.id`, которые совместно читают данные из топика. Kafka распределяет партиции топика между участниками группы так, что **каждая партиция в один момент времени читается ровно одним потребителем внутри одной группы**. Это позволяет горизонтально масштабировать скорость чтения вплоть до количества партиций в топике.

**25. Что такое реплика (Replica)? Чем роль Leader отличается от роли Follower?**  
Репликация в Kafka обеспечивает отказоустойчивость за счёт хранения копий каждой партиции на нескольких брокерах (задаётся параметром `Replication Factor`).
* **Leader-реплика** — единственная активная копия партиции, через которую проходят все операции записи от продюсеров и чтения от консьюмеров.
* **Follower-реплики** — пассивные копии на других брокерах, которые непрерывно реплицируют данные с лидера. Если брокер с лидером выходит из строя, один из синхронизированных фолловеров (ISR — In-Sync Replicas) автоматически становится новым лидером.

**26. Что такое ZooKeeper (или подсистема KRaft в новых версиях) и какова его роль в архитектуре Kafka?**  
Это координационный слой кластера, отвечающий за хранение метаданных (список топиков, конфигураций, ACL), отслеживание живых брокеров (heartbeats), выборы контроллера кластера и назначение лидеров партиций. В современных версиях Kafka внешний сервис ZooKeeper заменён встроенным протоколом консенсуса **KRaft (Kafka Raft)**, работающим непосредственно внутри процессов брокеров-контроллеров.

**27. Что такое Kafka Streams и как он отличается от написания Consumer-приложений?**  
Kafka Streams — это клиентская библиотека для создания потоковых приложений, преобразующих входные топики Kafka в выходные. В отличие от обычного `KafkaConsumer` (где разработчику нужно вручную программировать низкоуровневый цикл опроса, хранение состояния и агрегацию), Kafka Streams предоставляет высокоуровневый декларативный DSL для операций фильтрации (`filter`), трансформации (`map`), объединения потоков (`join`), оконных агрегаций (`windowing`) и управления локальным отказоустойчивым хранилищем состояний (State Stores).

**28. В чем заключаются фундаментальные архитектурные отличия между RabbitMQ и Apache Kafka (модель хранения, маршрутизация, состояние сообщений)?**  
| Критерий | RabbitMQ | Apache Kafka |
| :--- | :--- | :--- |
| **Модель хранения** | Временная буферизация в очереди; удаление сразу после `ack`. | Долговременный упорядоченный лог на диске (по времени или размеру retention). |
| **Маршрутизация** | Сложная и гибкая на стороне брокера (`direct`, `topic`, `fanout`, `headers`). | Простая: публикация в топик и выбор партиции по хешу ключа сообщения. |
| **Модель доставки и состояния** | **Push-модель**: брокер сам выталкивает сообщения и хранит статус каждого из них. | **Pull-модель**: консьюмер сам запрашивает данные с нужного смещения (`offset`). |

**29. Приведите примеры, в каких сценариях предпочтительнее использовать RabbitMQ, а в каких — Apache Kafka.**  
* **RabbitMQ предпочтителен:** для распределения фоновых задач (Work Queues: генерация PDF, отправка email), сложной маршрутизации бизнес-команд между микросервисами, реализации синхронных вызовов через RPC, приоритетных и отложенных очередей.
* **Apache Kafka предпочтительна:** для высоконагруженного сбора логов, метрик и телеметрии (IoT, кликстрим), реализации архитектур Event Sourcing и CQRS, построения конвейеров данных (CDC, ETL) и потоковой аналитики в реальном времени, где требуется высокая пропускная способность и возможность перечитывать исторические события (`replay`).

**30. Можно ли использовать RabbitMQ и Apache Kafka в одной архитектуре? Если да, то за какие зоны ответственности каждый из них будет отвечать?**  
Да, гибридное использование встречается в крупных системах очень часто:
* **Apache Kafka** выступает в роли центральной магистрали событий (**Event Backbone**): принимает огромные потоки сырых данных, хранит историю доменных событий между микросервисными контурами и питает аналитические хранилища (Data Lake / DWH).
* **RabbitMQ** используется локально внутри отдельных сервисных доменов как диспетчер задач (**Task Broker**): отвечает за гранулярную маршрутизацию команд, фоновые воркеры с повторными попытками (retries/DLX), приоритетные очереди уведомлений и взаимодействие с внешними устройствами по MQTT/STOMP.