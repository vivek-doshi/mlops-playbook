# Common Workflows

Standard retrieval paths for frequent engineering tasks.

## 1. Train, Evaluate, and Promote a Model

1. docs/golden-paths/mlops-workflow.md
2. docs/golden-paths/model-training-pipeline.md
3. dvc/pipeline-templates/train-eval-deploy.yaml
4. ci/github-actions/model-training/ and ci/github-actions/model-evaluation/
5. policy/model-approval/ and policy/data-governance/

## 2. Deploy and Monitor a Model

1. docs/golden-paths/model-serving.md
2. serving/
3. cd/kubernetes/environments/ and ci/github-actions/model-deployment/
4. docs/golden-paths/model-monitoring.md and monitoring/
5. finops/ and docs/guides/gpu-cost-governance.md

## 3. Run Batch or Orchestrated Inference

1. batch/README.md or pipelines/README.md
2. batch/ or pipelines/
3. cd/kubernetes/batch/ or cd/argo/pipelines/
4. policy/ and finops/

## 4. Respond to Model Incidents

1. docs/runbooks/
2. monitoring/alerts/ and monitoring/slos/
3. policy/model-approval/ for rollback and promotion controls
4. devops-playbook notifications and cluster observability interfaces (external dependency)
