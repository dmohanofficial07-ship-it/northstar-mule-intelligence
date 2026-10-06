import json
import logging

from kafka import KafkaConsumer
from sqlalchemy.exc import IntegrityError

from .config import settings
from .database import SessionLocal, init_db
from .models import EventReceipt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("northstar-event-worker")


def deserialize_event(value: bytes | None) -> dict[str, object]:
    return json.loads(value.decode("utf-8")) if value else {}


def run() -> None:
    init_db()
    consumer = KafkaConsumer(
        "northstar.risk-events",
        "northstar.case-events",
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="northstar-audit-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=deserialize_event,
    )
    logger.info("Event worker is listening for Northstar domain events")
    for message in consumer:
        event = message.value
        receipt = EventReceipt(
            topic=message.topic,
            partition=message.partition,
            offset=message.offset,
            event_type=event.get("event_type", "unknown"),
            entity_ref=event.get("transaction_ref") or event.get("case_ref") or "unknown",
            payload=json.dumps(event, default=str),
        )
        with SessionLocal() as db:
            try:
                db.add(receipt)
                db.commit()
                consumer.commit()
                logger.info("Stored %s for %s", receipt.event_type, receipt.entity_ref)
            except IntegrityError:
                db.rollback()
                consumer.commit()
                logger.info("Skipped already-processed event at %s:%s:%s", message.topic, message.partition, message.offset)


if __name__ == "__main__":
    run()
