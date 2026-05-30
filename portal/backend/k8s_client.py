"""
Purpose:
    Kubernetes client wrapper for the self-service portal.
    Reads Deployment and Pod status from the cluster; never modifies resources.

Usage:
    client = PortalK8sClient()
    deployments = client.list_model_deployments()

Dependencies:
    kubernetes>=29.0
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_MODEL_NAMESPACES = ["mlops-dev", "mlops-staging", "mlops-production"]


class PortalK8sClient:
    """Read-only Kubernetes client for deployment status used by the portal."""

    def __init__(self) -> None:
        try:
            from kubernetes import client as k8s_client, config as k8s_config

            try:
                k8s_config.load_incluster_config()
            except Exception:
                k8s_config.load_kube_config()
            self._apps_v1 = k8s_client.AppsV1Api()
            self._core_v1 = k8s_client.CoreV1Api()
        except ImportError as exc:
            logger.warning("kubernetes SDK not installed: %s", exc)
            self._apps_v1 = None
            self._core_v1 = None

    def list_model_deployments(self) -> list[dict[str, Any]]:
        if not self._apps_v1:
            return []
        results = []
        for ns in _MODEL_NAMESPACES:
            try:
                deployments = self._apps_v1.list_namespaced_deployment(namespace=ns)
                for d in deployments.items:
                    labels = d.metadata.labels or {}
                    results.append(
                        {
                            "name": d.metadata.name,
                            "namespace": ns,
                            "model_name": labels.get("model-name", ""),
                            "replicas": d.spec.replicas,
                            "ready_replicas": d.status.ready_replicas or 0,
                        }
                    )
            except Exception as exc:
                logger.warning("Failed to list deployments in %s: %s", ns, exc)
        return results

    def get_deployment_status(
        self, model_name: str, environment: str
    ) -> dict[str, Any] | None:
        if not self._apps_v1:
            return None
        namespace = f"mlops-{environment}"
        try:
            deployments = self._apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=f"model-name={model_name}",
            )
            if not deployments.items:
                return None
            d = deployments.items[0]
            return {
                "name": d.metadata.name,
                "namespace": namespace,
                "model_name": model_name,
                "environment": environment,
                "replicas": d.spec.replicas,
                "ready_replicas": d.status.ready_replicas or 0,
                "conditions": [
                    {"type": c.type, "status": c.status, "message": c.message}
                    for c in (d.status.conditions or [])
                ],
            }
        except Exception as exc:
            logger.warning("Failed to get deployment status: %s", exc)
            return None
