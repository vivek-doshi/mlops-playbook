"""
Purpose:
    Per-cloud health probe implementations for multi-cloud serving.
    Polls each cloud's native health endpoint every 30 seconds and records
    availability for use by the traffic router.

Usage:
    checker = HealthChecker(registry)
    status = checker.check_all()

Dependencies:
    requests>=2.31
    google-auth>=2.20 (GCP probe)
    azure-identity>=1.15 (Azure probe)
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Any

try:
    import requests
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install requests", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10  # seconds


@dataclass
class HealthStatus:
    cloud: str
    model_name: str
    url: str
    is_healthy: bool
    status_code: int | None = None
    error: str | None = None
    latency_ms: float | None = None


class HealthChecker:
    """Runs health probes against all registered endpoints."""

    def __init__(self, registry: Any) -> None:
        self._registry = registry

    def check_all(self) -> list[HealthStatus]:
        results = []
        for model_name in self._registry.all_models():
            for ep in self._registry.list_endpoints(model_name):
                status = self._probe(
                    cloud=ep["cloud"],
                    model_name=model_name,
                    endpoint=ep,
                )
                results.append(status)
        return results

    def _probe(self, cloud: str, model_name: str, endpoint: dict[str, Any]) -> HealthStatus:
        url = endpoint.get("url", "")
        probe_fn = {
            "aws": self._probe_sagemaker,
            "gcp": self._probe_vertex,
            "azure": self._probe_azure,
        }.get(cloud, self._probe_generic)

        return probe_fn(cloud=cloud, model_name=model_name, url=url)

    def _probe_sagemaker(self, cloud: str, model_name: str, url: str) -> HealthStatus:
        """SageMaker: GET /ping returns 200 when endpoint is healthy."""
        import time

        ping_url = url.rstrip("/") + "/ping"
        start = time.monotonic()
        try:
            resp = requests.get(ping_url, timeout=_REQUEST_TIMEOUT)
            latency_ms = (time.monotonic() - start) * 1000
            return HealthStatus(
                cloud=cloud,
                model_name=model_name,
                url=url,
                is_healthy=resp.status_code == 200,
                status_code=resp.status_code,
                latency_ms=round(latency_ms, 2),
            )
        except requests.RequestException as exc:
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=False, error=str(exc),
            )

    def _probe_vertex(self, cloud: str, model_name: str, url: str) -> HealthStatus:
        """
        Vertex AI: Query endpoint metadata via GCP REST API.
        Expects GOOGLE_APPLICATION_CREDENTIALS or ADC to be configured.
        """
        import time

        try:
            import google.auth
            import google.auth.transport.requests

            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            headers = {"Authorization": f"Bearer {credentials.token}"}
            start = time.monotonic()
            resp = requests.get(url, headers=headers, timeout=_REQUEST_TIMEOUT)
            latency_ms = (time.monotonic() - start) * 1000
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=resp.status_code == 200,
                status_code=resp.status_code,
                latency_ms=round(latency_ms, 2),
            )
        except ImportError:
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=False,
                error="google-auth not installed; run: pip install google-auth",
            )
        except Exception as exc:
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=False, error=str(exc),
            )

    def _probe_azure(self, cloud: str, model_name: str, url: str) -> HealthStatus:
        """
        Azure ML Managed Online Endpoint: POST /score with empty body.
        Expects AZURE_CLIENT_ID/TENANT_ID/CLIENT_SECRET or Managed Identity.
        """
        import time

        try:
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            token = credential.get_token("https://ml.azure.com/.default").token
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            start = time.monotonic()
            resp = requests.post(url, headers=headers, json={}, timeout=_REQUEST_TIMEOUT)
            latency_ms = (time.monotonic() - start) * 1000
            # Azure returns 400 (bad input) not 200 for health — both indicate endpoint is up
            is_healthy = resp.status_code in (200, 400)
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=is_healthy,
                status_code=resp.status_code,
                latency_ms=round(latency_ms, 2),
            )
        except ImportError:
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=False,
                error="azure-identity not installed; run: pip install azure-identity",
            )
        except Exception as exc:
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=False, error=str(exc),
            )

    def _probe_generic(self, cloud: str, model_name: str, url: str) -> HealthStatus:
        import time

        start = time.monotonic()
        try:
            resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
            latency_ms = (time.monotonic() - start) * 1000
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=resp.ok,
                status_code=resp.status_code,
                latency_ms=round(latency_ms, 2),
            )
        except requests.RequestException as exc:
            return HealthStatus(
                cloud=cloud, model_name=model_name, url=url,
                is_healthy=False, error=str(exc),
            )
