"""
Purpose:
    Downstream system notifier for batch inference jobs.
    Sends completion (or failure) notifications via configurable channels:
    Slack webhook, HTTP callback, and/or Azure Event Grid.

Usage:
    python batch/runner/downstream_notifier.py \\
        --job-config batch/jobs/fraud-detection-batch-job.yaml \\
        --status success \\
        --rows-scored 500000 \\
        --output-path s3://bucket/predictions/2024-01-15.parquet

Dependencies:
    pyyaml>=6.0
    requests>=2.31
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import requests
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

_TIMEOUT_SECONDS = 10


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


def _load_config(path: str) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- #
# Notification channels
# --------------------------------------------------------------------------- #


def notify_slack(webhook_url: str, payload: dict[str, Any]) -> None:
    """Send a Slack notification via incoming webhook."""
    status   = payload["status"]
    icon     = ":white_check_mark:" if status == "success" else ":x:"
    color    = "good" if status == "success" else "danger"
    job_name = payload.get("job_name", "unknown")
    env      = payload.get("environment", "unknown")

    slack_body = {
        "attachments": [
            {
                "color": color,
                "title": f"{icon} Batch job {status.upper()}: {job_name}",
                "fields": [
                    {"title": "Environment", "value": env,                          "short": True},
                    {"title": "Rows scored", "value": str(payload.get("rows_scored", "N/A")), "short": True},
                    {"title": "Output path", "value": payload.get("output_path", "N/A"), "short": False},
                    {"title": "Duration",    "value": f"{payload.get('latency_seconds', 0):.1f}s", "short": True},
                    {"title": "Timestamp",   "value": payload.get("timestamp", ""),     "short": True},
                ],
            }
        ]
    }

    resp = requests.post(webhook_url, json=slack_body, timeout=_TIMEOUT_SECONDS)
    resp.raise_for_status()
    logger.info("Slack notification sent (status=%d)", resp.status_code)


def notify_http_callback(callback_url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> None:
    """POST a JSON payload to an arbitrary HTTP callback URL."""
    resp = requests.post(
        callback_url,
        json=payload,
        headers=headers or {"Content-Type": "application/json"},
        timeout=_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    logger.info("HTTP callback sent to %s (status=%d)", callback_url, resp.status_code)


def notify_event_grid(endpoint: str, key: str, payload: dict[str, Any]) -> None:
    """Publish an event to Azure Event Grid."""
    event = [
        {
            "id":          f"batch-{payload.get('job_name', 'unknown')}-{payload.get('timestamp', '')}",
            "eventType":   f"MLOps.Batch.{payload['status'].capitalize()}",
            "subject":     f"batch/{payload.get('job_name', 'unknown')}",
            "eventTime":   payload.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "data":        payload,
            "dataVersion": "1.0",
        }
    ]

    resp = requests.post(
        endpoint,
        json=event,
        headers={"aeg-sas-key": key, "Content-Type": "application/json"},
        timeout=_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    logger.info("Event Grid event published (status=%d)", resp.status_code)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def send_notifications(
    config: dict[str, Any],
    status: str,
    rows_scored: int,
    output_path: str,
    latency_seconds: float = 0.0,
) -> None:
    """
    Dispatch notifications to all configured channels.

    Parameters
    ----------
    config:
        Parsed job YAML config.
    status:
        ``success`` or ``failure``.
    rows_scored:
        Number of rows scored in this run.
    output_path:
        Path to the output predictions file.
    latency_seconds:
        Total elapsed time for the batch run.
    """
    notifications = config.get("notifications", {})
    if not notifications:
        logger.info("No notifications configured — skipping.")
        return

    payload: dict[str, Any] = {
        "job_name":        config.get("job_name", "unknown"),
        "model_name":      config.get("model", {}).get("name", "unknown"),
        "environment":     config.get("environment", "unknown"),
        "status":          status,
        "rows_scored":     rows_scored,
        "output_path":     output_path,
        "latency_seconds": latency_seconds,
        "timestamp":       datetime.now(timezone.utc).isoformat(),
    }

    # Slack
    slack_url = notifications.get("slack_webhook_url") or os.environ.get("SLACK_BATCH_WEBHOOK_URL")
    if slack_url:
        try:
            notify_slack(slack_url, payload)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Slack notification failed: %s", exc)

    # HTTP callback
    callback = notifications.get("http_callback")
    if callback:
        url     = callback.get("url")
        headers = callback.get("headers", {})
        if url:
            try:
                notify_http_callback(url, payload, headers)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("HTTP callback failed: %s", exc)

    # Azure Event Grid
    eg = notifications.get("event_grid")
    if eg:
        endpoint = eg.get("endpoint")
        key      = eg.get("key") or os.environ.get("EVENT_GRID_KEY")
        if endpoint and key:
            try:
                notify_event_grid(endpoint, key, payload)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Event Grid notification failed: %s", exc)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch downstream notifier.")
    parser.add_argument("--job-config",       required=True,  help="Path to job config YAML")
    parser.add_argument("--status",           required=True,  choices=["success", "failure"])
    parser.add_argument("--rows-scored",      type=int,       default=0)
    parser.add_argument("--output-path",      default="")
    parser.add_argument("--latency-seconds",  type=float,     default=0.0)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = _load_config(args.job_config)
    send_notifications(
        config,
        status=args.status,
        rows_scored=args.rows_scored,
        output_path=args.output_path,
        latency_seconds=args.latency_seconds,
    )
