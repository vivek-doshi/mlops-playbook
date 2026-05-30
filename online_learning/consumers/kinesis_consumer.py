"""
Purpose:
    AWS Kinesis stream consumer for online learning mini-batches.
    Uses boto3 to poll a Kinesis Data Stream shard and accumulate records
    into mini-batches of at least min_batch_size records before yielding.

Usage:
    consumer = KinesisStreamConsumer(
        config={"stream_name": "ml-feedback", "region": "us-east-1", "shard_id": "shardId-000000000000"},
        min_batch_size=500,
    )
    for batch in consumer.batches():
        updater.apply(batch)

Dependencies:
    boto3>=1.26
"""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any, Generator

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install boto3", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

_POLL_INTERVAL_SECONDS = 1.0
_MAX_RECORDS_PER_CALL = 500


class KinesisStreamConsumer:
    """
    Consumes records from an AWS Kinesis Data Stream shard.

    Parameters
    ----------
    config : dict
        Required keys: stream_name, region, shard_id.
        Optional: shard_iterator_type (default "LATEST").
    min_batch_size : int
        Minimum records per yielded batch (default 500).
    """

    def __init__(self, config: dict[str, Any], min_batch_size: int = 500) -> None:
        self._stream_name = config["stream_name"]
        self._shard_id = config["shard_id"]
        self._min_batch_size = min_batch_size
        self._client = boto3.client("kinesis", region_name=config["region"])
        self._shard_iterator_type = config.get("shard_iterator_type", "LATEST")
        logger.info(
            "KinesisStreamConsumer ready — stream=%s shard=%s",
            self._stream_name,
            self._shard_id,
        )

    def _get_shard_iterator(self) -> str:
        response = self._client.get_shard_iterator(
            StreamName=self._stream_name,
            ShardId=self._shard_id,
            ShardIteratorType=self._shard_iterator_type,
        )
        return response["ShardIterator"]

    def batches(self) -> Generator[list[dict[str, Any]], None, None]:
        """Poll Kinesis shard and yield mini-batches."""
        shard_iterator = self._get_shard_iterator()
        buffer: list[dict[str, Any]] = []
        try:
            while shard_iterator:
                try:
                    response = self._client.get_records(
                        ShardIterator=shard_iterator,
                        Limit=_MAX_RECORDS_PER_CALL,
                    )
                except (BotoCoreError, ClientError) as exc:
                    logger.error("Kinesis get_records error: %s", exc)
                    break
                shard_iterator = response.get("NextShardIterator", "")
                for record in response["Records"]:
                    try:
                        buffer.append(json.loads(record["Data"]))
                    except json.JSONDecodeError:
                        logger.warning("Skipping non-JSON Kinesis record.")
                if len(buffer) >= self._min_batch_size:
                    yield buffer
                    buffer = []
                time.sleep(_POLL_INTERVAL_SECONDS)
        finally:
            if buffer:
                yield buffer
