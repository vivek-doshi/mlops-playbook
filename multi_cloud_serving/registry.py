"""
Purpose:
    Endpoint catalog for multi-cloud serving.  Reads Terraform output files from
    the three cloud providers and maintains a live registry of deployed model
    endpoints (URL, cloud, region, version, serving runtime).

Usage:
    registry = EndpointRegistry()
    registry.refresh()
    endpoints = registry.list_endpoints("my-model")

Dependencies:
    mlflow>=2.14
    pyyaml>=6.0
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

try:
    import mlflow
    import yaml
except ImportError as exc:
    print(f"ERROR: {exc}\nInstall with: pip install mlflow pyyaml", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

_TERRAFORM_OUTPUT_PATHS: dict[str, str] = {
    "aws": "terraform/aws-sagemaker/outputs.json",
    "gcp": "terraform/gcp-vertex-ai/outputs.json",
    "azure": "terraform/azure-ml/outputs.json",
}


class EndpointRegistry:
    """
    Builds an in-memory catalog of multi-cloud serving endpoints from Terraform outputs.

    Each Terraform outputs.json must contain a key ``model_endpoints`` whose value is a
    list of objects with fields: model_name, url, region, version, runtime.
    """

    def __init__(
        self,
        terraform_root: str | Path = ".",
        tracking_uri: str = "http://localhost:5000",
    ) -> None:
        self._root = Path(terraform_root)
        self._catalog: dict[str, list[dict[str, Any]]] = {}
        mlflow.set_tracking_uri(tracking_uri)

    def refresh(self) -> None:
        """Reload endpoint catalog from Terraform output files."""
        self._catalog = {}
        for cloud, relative_path in _TERRAFORM_OUTPUT_PATHS.items():
            tf_output_path = self._root / relative_path
            if not tf_output_path.exists():
                logger.warning(
                    "Terraform output not found for %s at %s — skipping.", cloud, tf_output_path
                )
                continue
            with tf_output_path.open() as fh:
                try:
                    outputs = json.load(fh)
                except json.JSONDecodeError as exc:
                    logger.error("Failed to parse Terraform output %s: %s", tf_output_path, exc)
                    continue

            endpoints = outputs.get("model_endpoints", {}).get("value", [])
            for ep in endpoints:
                model_name = ep.get("model_name", "unknown")
                if model_name not in self._catalog:
                    self._catalog[model_name] = []
                self._catalog[model_name].append(
                    {
                        "cloud": cloud,
                        "url": ep.get("url"),
                        "region": ep.get("region"),
                        "version": ep.get("version"),
                        "runtime": ep.get("runtime"),
                    }
                )

        logger.info("Endpoint catalog refreshed: %d models.", len(self._catalog))

    def list_endpoints(self, model_name: str) -> list[dict[str, Any]]:
        """Return all live endpoints for a model across clouds."""
        return self._catalog.get(model_name, [])

    def get_endpoint_url(self, model_name: str, cloud: str) -> str | None:
        """Return the URL for a specific model/cloud combination."""
        for ep in self.list_endpoints(model_name):
            if ep["cloud"] == cloud:
                return ep["url"]
        return None

    def all_models(self) -> list[str]:
        return list(self._catalog.keys())

    def to_routing_config(self, model_name: str, weights: dict[str, float] | None = None) -> dict[str, Any]:
        """
        Generate a routing config dict from registered endpoints.

        Parameters
        ----------
        model_name : str
        weights : dict optional
            Per-cloud traffic weight.  Defaults to equal split.
        """
        endpoints = self.list_endpoints(model_name)
        if not endpoints:
            raise ValueError(f"No endpoints registered for model '{model_name}'")

        default_weight = round(1.0 / len(endpoints), 2)
        config: dict[str, Any] = {
            "model_name": model_name,
            "timeout_seconds": 30,
            "endpoints": {},
        }
        for ep in endpoints:
            cloud = ep["cloud"]
            config["endpoints"][cloud] = {
                "url": ep["url"],
                "weight": (weights or {}).get(cloud, default_weight),
                "region": ep.get("region"),
                "runtime": ep.get("runtime"),
            }
        return config
