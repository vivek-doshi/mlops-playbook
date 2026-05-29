"""
Purpose:
    Model deployment pipeline component.
    Promotes a Staging model to Production in MLflow and optionally
    triggers a Kubernetes rollout via kubectl.

Usage:
    Called as a pipeline step.  Standalone:
        python pipelines/components/deployment/component.py \\
            --config-file pipelines/config/fraud-detection.yaml

Dependencies:
    mlflow>=2.11
    pyyaml>=6.0
"""

from __future__ import annotations

import argparse
import logging
import subprocess
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient
import yaml

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def deploy(config: dict[str, Any]) -> None:
    """Promote Staging model to Production and (optionally) rollout k8s deployment."""
    model_name   = config.get("model_name",         "my-model")
    tracking     = config.get("mlflow_tracking_uri")
    k8s_deploy   = config.get("kubernetes_deployment")

    if tracking:
        mlflow.set_tracking_uri(tracking)

    client = MlflowClient()

    # Find the latest Staging version.
    staging_versions = client.get_latest_versions(model_name, stages=["Staging"])
    if not staging_versions:
        raise RuntimeError(f"No model version in Staging for '{model_name}'")

    version = staging_versions[0].version

    client.transition_model_version_stage(
        name=model_name, version=version, stage="Production",
        archive_existing_versions=True,
    )
    logger.info("Promoted %s v%s → Production", model_name, version)

    # Optional: trigger a Kubernetes rollout.
    if k8s_deploy:
        namespace   = k8s_deploy.get("namespace",  f"{model_name}-production")
        deploy_name = k8s_deploy.get("name",       f"{model_name}-serving")
        image       = k8s_deploy.get("image_template", "").format(version=version)

        if image:
            cmd = [
                "kubectl", "set", "image",
                f"deployment/{deploy_name}",
                f"serving={image}",
                "-n", namespace,
            ]
            logger.info("Running: %s", " ".join(cmd))
            subprocess.run(cmd, check=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deployment component.")
    parser.add_argument("--config-file", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args   = _parse_args()
    config = yaml.safe_load(open(args.config_file))
    deploy(config)
