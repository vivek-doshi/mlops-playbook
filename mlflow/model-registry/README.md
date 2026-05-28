# MLflow Model Registry

Use the registry to promote approved model versions through Staging and Production.

Recommended flow:

1. Log model artifacts and metrics from CI training runs.
2. Run evaluation and policy checks.
3. Register model version if checks pass.
4. Promote only approved versions to Production.
