"""
Purpose:
    Traffic weight routing and automatic failover logic for multi-cloud model serving.
    Routes prediction requests across AWS SageMaker, GCP Vertex AI, and Azure ML
    endpoints using configurable weights.  Automatically shifts traffic away from
    unhealthy endpoints when error rate exceeds the failover threshold.

Usage:
    router = MultiCloudRouter(model_name="my-model", config_dir="multi_cloud_serving/routing-config/")
    result = router.predict(payload)

Dependencies:
    requests>=2.31
    pyyaml>=6.0
    mlflow>=2.14
"""

from __future__ import annotations

import logging
import random
import sys
import time
from pathlib import Path
from typing import Any

try:
    import mlflow
    import requests
    import yaml
except ImportError as exc:
    print(
        f"ERROR: {exc}\nInstall with: pip install requests pyyaml mlflow",
        file=sys.stderr,
    )
    sys.exit(1)

logger = logging.getLogger(__name__)

_FAILOVER_ERROR_RATE_THRESHOLD = 0.05  # 5% triggers failover
_FAILOVER_WINDOW_SECONDS = 120         # 2-minute window
_HEALTH_CHECK_INTERVAL_SECONDS = 30


class EndpointStats:
    """Rolling error-rate tracker for a single endpoint."""

    def __init__(self, window_seconds: int = _FAILOVER_WINDOW_SECONDS) -> None:
        self._window = window_seconds
        self._requests: list[tuple[float, bool]] = []  # (timestamp, is_error)

    def record(self, is_error: bool) -> None:
        now = time.monotonic()
        self._requests.append((now, is_error))
        cutoff = now - self._window
        self._requests = [(t, e) for t, e in self._requests if t >= cutoff]

    @property
    def error_rate(self) -> float:
        if not self._requests:
            return 0.0
        errors = sum(1 for _, is_error in self._requests if is_error)
        return errors / len(self._requests)


class MultiCloudRouter:
    """Route predictions across cloud endpoints with automatic failover."""

    def __init__(
        self,
        model_name: str,
        config_dir: str | Path = "multi_cloud_serving/routing-config/",
        tracking_uri: str = "http://localhost:5000",
    ) -> None:
        self._model_name = model_name
        self._config = self._load_config(Path(config_dir), model_name)
        self._stats: dict[str, EndpointStats] = {
            cloud: EndpointStats()
            for cloud in self._config.get("endpoints", {})
        }
        mlflow.set_tracking_uri(tracking_uri)

    def _load_config(self, config_dir: Path, model_name: str) -> dict[str, Any]:
        config_file = config_dir / f"{model_name}.yaml"
        if not config_file.exists():
            raise FileNotFoundError(
                f"No routing config found at {config_file}. "
                f"Create it using the schema in {config_dir / '_config-schema.yaml'}"
            )
        with config_file.open() as fh:
            return yaml.safe_load(fh)

    def _healthy_weights(self) -> dict[str, float]:
        """Return per-cloud weights, zeroing out unhealthy endpoints."""
        weights = {}
        for cloud, spec in self._config.get("endpoints", {}).items():
            if self._stats[cloud].error_rate > _FAILOVER_ERROR_RATE_THRESHOLD:
                logger.warning(
                    "Endpoint %s/%s error_rate=%.2f%% — removing from pool",
                    self._model_name,
                    cloud,
                    self._stats[cloud].error_rate * 100,
                )
                weights[cloud] = 0.0
            else:
                weights[cloud] = float(spec.get("weight", 0))

        total = sum(weights.values())
        if total == 0:
            raise RuntimeError(
                f"All endpoints for {self._model_name} are unhealthy — cannot route traffic."
            )
        return {c: w / total for c, w in weights.items()}

    def _select_cloud(self) -> str:
        weights = self._healthy_weights()
        clouds = list(weights.keys())
        probabilities = [weights[c] for c in clouds]
        return random.choices(clouds, weights=probabilities, k=1)[0]

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a prediction request to the selected cloud endpoint."""
        cloud = self._select_cloud()
        endpoint_url = self._config["endpoints"][cloud]["url"]

        try:
            response = requests.post(
                endpoint_url,
                json=payload,
                timeout=self._config.get("timeout_seconds", 30),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            is_error = False
            result = response.json()
            result["_serving_cloud"] = cloud
            return result
        except (requests.RequestException, ValueError) as exc:
            is_error = True
            logger.error("Prediction error on %s/%s: %s", self._model_name, cloud, exc)
            self._handle_failover(cloud)
            raise
        finally:
            self._stats[cloud].record(is_error)

    def _handle_failover(self, failed_cloud: str) -> None:
        if self._stats[failed_cloud].error_rate > _FAILOVER_ERROR_RATE_THRESHOLD:
            logger.error(
                "CrossCloudFailoverTriggered: %s is unhealthy (error_rate=%.2f%%). "
                "Traffic shifted to remaining endpoints.",
                failed_cloud,
                self._stats[failed_cloud].error_rate * 100,
            )

    def health_summary(self) -> dict[str, dict[str, Any]]:
        return {
            cloud: {
                "error_rate_pct": round(self._stats[cloud].error_rate * 100, 2),
                "healthy": self._stats[cloud].error_rate <= _FAILOVER_ERROR_RATE_THRESHOLD,
            }
            for cloud in self._stats
        }
