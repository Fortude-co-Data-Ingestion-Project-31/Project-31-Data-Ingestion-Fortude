import json
import os


def publish_documents(documents):
    """Publish canonical documents to the configured Kafka topic."""
    try:
        from kafka import KafkaProducer
    except ImportError as error:
        raise RuntimeError(
            "Kafka output requires the kafka-python package."
        ) from error

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "fortude.ingestion")
    producer = KafkaProducer(
        bootstrap_servers=[server.strip() for server in bootstrap_servers.split(",")],
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )

    try:
        for document in documents:
            producer.send(topic, value=document)
        producer.flush()
    finally:
        producer.close()

    return topic