"""
Phase 1 lineage metadata client.

Uses SQLite by default and executes writes against the schema in schema.sql.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class MetadataStoreClient:
    """Minimal lineage client for dataset/run/model/deployment records."""

    def __init__(self, db_path: str = "mlflow/metadata-store/lineage.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def close(self) -> None:
        self.conn.close()

    def bootstrap_schema(self, schema_path: str = "mlflow/metadata-store/schema.sql") -> None:
        schema_sql = Path(schema_path).read_text(encoding="utf-8")
        self.conn.executescript(schema_sql)
        self.conn.commit()

    def register_dataset(
        self,
        dataset_id: str,
        dataset_name: str,
        dataset_version: str,
        dvc_hash: str,
        storage_uri: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO lineage_datasets (dataset_id, dataset_name, dataset_version, dvc_hash, storage_uri)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(dataset_id) DO UPDATE SET
              dataset_name=excluded.dataset_name,
              dataset_version=excluded.dataset_version,
              dvc_hash=excluded.dvc_hash,
              storage_uri=excluded.storage_uri
            """,
            (dataset_id, dataset_name, dataset_version, dvc_hash, storage_uri),
        )
        self.conn.commit()

    def register_training_run(
        self,
        run_id: str,
        model_name: str,
        git_commit_sha: str,
        trigger_source: str,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO lineage_training_runs (run_id, model_name, git_commit_sha, trigger_source, metrics_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
              model_name=excluded.model_name,
              git_commit_sha=excluded.git_commit_sha,
              trigger_source=excluded.trigger_source,
              metrics_json=excluded.metrics_json
            """,
            (run_id, model_name, git_commit_sha, trigger_source, json.dumps(metrics or {})),
        )
        self.conn.commit()

    def link_run_input(self, run_id: str, dataset_id: str, featureset_id: str | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO lineage_run_inputs (run_id, dataset_id, featureset_id)
            VALUES (?, ?, ?)
            ON CONFLICT(run_id, dataset_id) DO UPDATE SET
              featureset_id=excluded.featureset_id
            """,
            (run_id, dataset_id, featureset_id),
        )
        self.conn.commit()

    def register_model_version(
        self,
        model_version_id: str,
        model_name: str,
        model_version: str,
        mlflow_run_id: str,
        stage: str,
        validation_status: str,
        model_uri: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO lineage_model_versions (
              model_version_id, model_name, model_version, mlflow_run_id, stage, validation_status, model_uri
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(model_version_id) DO UPDATE SET
              model_name=excluded.model_name,
              model_version=excluded.model_version,
              mlflow_run_id=excluded.mlflow_run_id,
              stage=excluded.stage,
              validation_status=excluded.validation_status,
              model_uri=excluded.model_uri
            """,
            (
                model_version_id,
                model_name,
                model_version,
                mlflow_run_id,
                stage,
                validation_status,
                model_uri,
            ),
        )
        self.conn.commit()

    def register_deployment(
        self,
        deployment_id: str,
        model_version_id: str,
        serving_runtime: str,
        deployment_mode: str,
        environment: str,
        rollout_status: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO lineage_deployments (
              deployment_id, model_version_id, serving_runtime, deployment_mode, environment, rollout_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(deployment_id) DO UPDATE SET
              model_version_id=excluded.model_version_id,
              serving_runtime=excluded.serving_runtime,
              deployment_mode=excluded.deployment_mode,
              environment=excluded.environment,
              rollout_status=excluded.rollout_status
            """,
            (
                deployment_id,
                model_version_id,
                serving_runtime,
                deployment_mode,
                environment,
                rollout_status,
            ),
        )
        self.conn.commit()

    def get_run_lineage(self, run_id: str) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT
              r.run_id,
              r.model_name,
              r.git_commit_sha,
              r.trigger_source,
              i.dataset_id,
              d.dvc_hash,
              i.featureset_id
            FROM lineage_training_runs r
            LEFT JOIN lineage_run_inputs i ON i.run_id = r.run_id
            LEFT JOIN lineage_datasets d ON d.dataset_id = i.dataset_id
            WHERE r.run_id = ?
            """,
            (run_id,),
        )
        return cur.fetchall()


if __name__ == "__main__":
    client = MetadataStoreClient()
    client.bootstrap_schema()
    client.close()
