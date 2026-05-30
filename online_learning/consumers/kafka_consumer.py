"""
Purpose:
    Kafka stream consumer for online learning mini-batches.
    Reads records from one or more Kafka topics and accumulates them into
    mini-batches of at least min_batch_size records before yielding.

Usage:
    consumer = KafkaStreamConsumer(
        config={"bootstrap_servers": "localhost:9092", "topic": "predictions", "group_id": "ol-group"},
        min_batch_size=500,
    )
    for batch in consumer.batches():
        updater.apply(batch)

Dependencies:
    kafka-python>=2.0
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Generator

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
except ImportError as exc:
    print(
        f"ERROR: {exc}\nInstall with: pip install kafka-python",
        file=sys.stderr,
    )
    sys.exit(1)

logger = logging.getLogger(__name__)


class KafkaStreamConsumer:
    """
    Consumes records from Kafka and yields mini-batches.

    Parameters
    ----------
    config : dict
        Required keys: bootstrap_servers, topic, group_id.
        Optional: auto_offset_reset (default "latest"), consumer_timeout_ms (default 1000).
    min_batch_size : int
        Minimum records per yielded batch (default 500).
    """

    def __init__(self, config: dict[str, Any], min_batch_size: int = 500) -> None:
        self._topic = config["topic"]
        self._min_batch_size = min_batch_size
        self._consumer = KafkaConsumer(
            self._topic,
            bootstrap_servers=config["bootstrap_servers"],
            group_id=config["group_id"],
            auto_offset_reset=config.get("auto_offset_reset", "latest"),
            consumer_timeout_ms=config.get("consumer_timeout_ms", 1000),
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        logger.info("KafkaStreamConsumer connected to topic '%s'", self._topic)

    def batches(self) -> Generator[list[dict[str, Any]], None, None]:
        """Yield mini-batches of at least min_batch_size records."""
        buffer: list[dict[str, Any]] = []
        try:
            for message in self._consumer:
                buffer.append(message.value)
                if len(buffer) >= self._min_batch_size:
                    yield buffer
                    buffer = []
        except KafkaError as exc:
            logger.error("KafkaConsumer error: %s", exc)
        finally:
            if buffer:
                logger.info("Flushing partial batch of %d records on close.", len(buffer))
                yield buffer

    def close(self) -> None:
        self._consumer.close()
        logger.info("KafkaStreamConsumer closed.")
