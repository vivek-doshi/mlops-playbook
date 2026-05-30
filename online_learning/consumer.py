"""
Purpose:
    Kafka/Kinesis/Pub/Sub stream consumer dispatcher for online learning.
    Reads mini-batches from a streaming source and yields them to the updater.
    Delegates to cloud-specific consumer implementations in consumers/.

Usage:
    consumer = StreamConsumer(source="kafka", config={"bootstrap_servers": "localhost:9092", ...})
    for batch in consumer.batches():
        updater.apply(batch)

Dependencies:
    pyyaml>=6.0
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Generator

try:
    import yaml
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

_SUPPORTED_SOURCES = ("kafka", "kinesis", "pubsub")


class StreamConsumer:
    """
    Unified stream consumer that dispatches to a cloud-specific implementation.

    Parameters
    ----------
    source : str
        Stream source: "kafka" | "kinesis" | "pubsub"
    config : dict
        Source-specific configuration passed to the consumer implementation.
    min_batch_size : int
        Minimum records per mini-batch.  Default 500.
    """

    def __init__(
        self,
        source: str,
        config: dict[str, Any],
        min_batch_size: int = 500,
    ) -> None:
        if source not in _SUPPORTED_SOURCES:
            raise ValueError(f"source must be one of {_SUPPORTED_SOURCES}, got '{source}'")
        self._source = source
        self._config = config
        self._min_batch_size = min_batch_size
        self._impl = self._load_impl(source, config, min_batch_size)

    @staticmethod
    def _load_impl(source: str, config: dict[str, Any], min_batch_size: int) -> Any:
        if source == "kafka":
            from online_learning.consumers.kafka_consumer import KafkaStreamConsumer
            return KafkaStreamConsumer(config=config, min_batch_size=min_batch_size)
        if source == "kinesis":
            from online_learning.consumers.kinesis_consumer import KinesisStreamConsumer
            return KinesisStreamConsumer(config=config, min_batch_size=min_batch_size)
        # pubsub
        from online_learning.consumers.pubsub_consumer import PubSubStreamConsumer
        return PubSubStreamConsumer(config=config, min_batch_size=min_batch_size)

    def batches(self) -> Generator[list[dict[str, Any]], None, None]:
        """Yield mini-batches of records from the stream."""
        yield from self._impl.batches()

    def close(self) -> None:
        if hasattr(self._impl, "close"):
            self._impl.close()
