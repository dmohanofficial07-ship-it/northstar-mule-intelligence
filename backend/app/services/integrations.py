import json
import logging
from typing import Any

from kafka import KafkaProducer
from neo4j import GraphDatabase
from redis import Redis

from ..config import settings

logger = logging.getLogger(__name__)


class Integrations:
    def __init__(self) -> None:
        self.redis: Redis | None = None
        self.kafka: KafkaProducer | None = None
        self.neo4j = None

    def connect(self) -> None:
        try:
            redis_client = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
            redis_client.ping()
            self.redis = redis_client
        except Exception as exc:
            logger.warning("Redis unavailable; caching disabled: %s", exc)
            self.redis = None
        try:
            self.kafka = KafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
                request_timeout_ms=1500,
                api_version_auto_timeout_ms=1500,
            )
        except Exception as exc:
            logger.warning("Kafka unavailable; event publishing disabled: %s", exc)
            self.kafka = None
        try:
            self.neo4j = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
                connection_timeout=2,
            )
            self.neo4j.verify_connectivity()
        except Exception as exc:
            logger.warning("Neo4j unavailable; graph fallback enabled: %s", exc)
            self.neo4j = None

    def get_cached(self, key: str) -> Any | None:
        if not self.redis:
            return None
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as exc:
            logger.warning("Redis read failed: %s", exc)
            return None

    def set_cached(self, key: str, value: Any, ttl: int = 30) -> None:
        if self.redis:
            try:
                self.redis.setex(key, ttl, json.dumps(value, default=str))
            except Exception as exc:
                logger.warning("Redis write failed: %s", exc)

    def invalidate(self, *keys: str) -> None:
        if self.redis and keys:
            try:
                self.redis.delete(*keys)
            except Exception as exc:
                logger.warning("Redis invalidation failed: %s", exc)

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        if self.kafka:
            try:
                self.kafka.send(topic, event)
                self.kafka.flush(timeout=2)
            except Exception as exc:
                logger.warning("Kafka publish failed for %s: %s", topic, exc)

    def statuses(self) -> dict[str, str]:
        return {
            "redis": "connected" if self.redis else "degraded",
            "kafka": "connected" if self.kafka else "degraded",
            "neo4j": "connected" if self.neo4j else "fallback",
        }

    def close(self) -> None:
        if self.kafka:
            self.kafka.close(timeout=2)
        if self.redis:
            self.redis.close()
        if self.neo4j:
            self.neo4j.close()


integrations = Integrations()
