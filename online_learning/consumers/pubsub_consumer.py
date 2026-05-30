"""
Purpose:
    GCP Pub/Sub consumer for online learning mini-batches.
    Pulls messages from a Pub/Sub subscription and accumulates them into
    mini-batches of at least min_batch_size records before yielding.
    Acknowledges messages only after the batch is successfully yielded.

Usage:
    consumer = PubSubStreamConsumer(
        config={"project_id": "my-project", "subscription": "ml-feedback-sub"},
        min_batch_size=500,
    )
    for batch in consumer.batches():
        updater.apply(batch)

Dependencies:
    google-cloud-pubsub>=2.18
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Generator

try:
    from google.cloud import pubsub_v1
    from google.api_core.exceptions import GoogleAPIError
except ImportError as exc:
    print(
        f"ERROR: {exc}\nInstall with: pip install google-cloud-pubsub",
        file=sys.stderr,
    )
    sys.exit(1)

logger = logging.getLogger(__name__)

_MAX_MESSAGES_PER_PULL = 500


class PubSubStreamConsumer:
    """
    Pulls messages from a GCP Pub/Sub subscription.

    Parameters
    ----------
    config : dict
        Required keys: project_id, subscription.
    min_batch_size : int
        Minimum records per yielded batch (default 500).
    """

    def __init__(self, config: dict[str, Any], min_batch_size: int = 500) -> None:
        self._project_id = config["project_id"]
        self._subscription = config["subscription"]
        self._min_batch_size = min_batch_size
        self._client = pubsub_v1.SubscriberClient()
        self._subscription_path = self._client.subscription_path(
            self._project_id, self._subscription
        )
        logger.info(
            "PubSubStreamConsumer ready — subscription=%s",
            self._subscription_path,
        )

    def batches(self) -> Generator[list[dict[str, Any]], None, None]:
        """Pull from Pub/Sub and yield mini-batches, acking after each yield."""
        buffer: list[dict[str, Any]] = []
        ack_ids: list[str] = []
        try:
            while True:
                try:
                    response = self._client.pull(
                        request={
                            "subscription": self._subscription_path,
                            "max_messages": _MAX_MESSAGES_PER_PULL,
                        }
                    )
                except GoogleAPIError as exc:
                    logger.error("PubSub pull error: %s", exc)
                    break
                for msg in response.received_messages:
                    try:
                        buffer.append(json.loads(msg.message.data.decode("utf-8")))
                        ack_ids.append(msg.ack_id)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        logger.warning("Skipping un-parseable Pub/Sub message.")
                if len(buffer) >= self._min_batch_size:
                    yield buffer
                    # Ack only after successful yield
                    self._client.acknowledge(
                        request={
                            "subscription": self._subscription_path,
                            "ack_ids": ack_ids,
                        }
                    )
                    buffer = []
                    ack_ids = []
        finally:
            if buffer:
                yield buffer
                if ack_ids:
                    self._client.acknowledge(
                        request={
                            "subscription": self._subscription_path,
                            "ack_ids": ack_ids,
                        }
                    )

    def close(self) -> None:
        self._client.close()
        logger.info("PubSubStreamConsumer closed.")
