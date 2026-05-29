-- Phase 1 metadata schema for model/data lineage.
-- Compatible with SQLite and PostgreSQL-compatible SQL engines.

CREATE TABLE IF NOT EXISTS lineage_datasets (
  dataset_id TEXT PRIMARY KEY,
  dataset_name TEXT NOT NULL,
  dataset_version TEXT NOT NULL,
  dvc_hash TEXT NOT NULL,
  storage_uri TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lineage_featuresets (
  featureset_id TEXT PRIMARY KEY,
  featureset_name TEXT NOT NULL,
  featureset_version TEXT NOT NULL,
  source_dataset_id TEXT NOT NULL,
  feast_view_name TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (source_dataset_id) REFERENCES lineage_datasets(dataset_id)
);

CREATE TABLE IF NOT EXISTS lineage_training_runs (
  run_id TEXT PRIMARY KEY,
  model_name TEXT NOT NULL,
  git_commit_sha TEXT NOT NULL,
  trigger_source TEXT NOT NULL,
  metrics_json TEXT NOT NULL DEFAULT '{}',
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);

CREATE TABLE IF NOT EXISTS lineage_run_inputs (
  run_id TEXT NOT NULL,
  dataset_id TEXT NOT NULL,
  featureset_id TEXT,
  PRIMARY KEY (run_id, dataset_id),
  FOREIGN KEY (run_id) REFERENCES lineage_training_runs(run_id),
  FOREIGN KEY (dataset_id) REFERENCES lineage_datasets(dataset_id),
  FOREIGN KEY (featureset_id) REFERENCES lineage_featuresets(featureset_id)
);

CREATE TABLE IF NOT EXISTS lineage_model_versions (
  model_version_id TEXT PRIMARY KEY,
  model_name TEXT NOT NULL,
  model_version TEXT NOT NULL,
  mlflow_run_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  validation_status TEXT NOT NULL,
  model_uri TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (model_name, model_version),
  FOREIGN KEY (mlflow_run_id) REFERENCES lineage_training_runs(run_id)
);

CREATE TABLE IF NOT EXISTS lineage_deployments (
  deployment_id TEXT PRIMARY KEY,
  model_version_id TEXT NOT NULL,
  serving_runtime TEXT NOT NULL,
  deployment_mode TEXT NOT NULL,
  environment TEXT NOT NULL,
  rollout_status TEXT NOT NULL,
  deployed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (model_version_id) REFERENCES lineage_model_versions(model_version_id)
);

CREATE INDEX IF NOT EXISTS idx_lineage_run_inputs_dataset ON lineage_run_inputs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_lineage_model_versions_stage ON lineage_model_versions(stage);
CREATE INDEX IF NOT EXISTS idx_lineage_deployments_runtime ON lineage_deployments(serving_runtime);
