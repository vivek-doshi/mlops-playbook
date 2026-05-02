# How to Adapt This Playbook for Your Own Dataset

This repository is designed as a starter template using a synthetic "churn prediction" dataset. To use this playbook for your own real-world machine learning project, follow the step-by-step guide below.

---

## Step 1: Bring Your Own Data

The current data pipeline relies on a synthetic generation script. You need to replace this with your actual data source (e.g., querying a database, downloading from S3, or reading a local CSV).

1. **Delete the synthetic generator:**
   Remove `src/data/make_dataset.py`.
2. **Write your extraction logic:**
   Create a new script (e.g., `src/data/extract.py`) that pulls your raw data and saves it to `data/raw/dataset.csv`.
3. **Update the Ingestion Pipeline:**
   Modify `pipelines/data_ingestion.py` to call your new extraction script instead of the synthetic generator.

## Step 2: Define Your Data Schema

Data validation ensures that bad data doesn't silently poison your model or crash your inference API.

1. **Update Pydantic Schema:**
   Open `src/data/validation.py` and modify the `DataSchema` class. Replace `feature_0`, `feature_1`, etc., with your actual column names and their expected data types (e.g., `age: int`, `income: float`).
2. **Update Inference Request Schema:**
   Open `src/inference/api.py` and update the `InferenceRequest` class to match the features your API clients will send.

## Step 3: Implement Feature Engineering

Production ML requires feature transformations to be saved and applied identically during training and inference. We handle this using `scikit-learn` Pipelines.

1. **Modify the Pipeline:**
   Open `src/features/build_features.py`. Replace the basic `StandardScaler` with your custom transformations.
   *Example: Add `OneHotEncoder` for categorical variables, or `SimpleImputer` for missing values.*
2. **Ensure it returns a Pipeline:**
   The function `build_feature_pipeline()` must return a fitted `sklearn.pipeline.Pipeline` object so it can be saved by `joblib`.

## Step 4: Swap the ML Algorithm (Optional)

The template defaults to a `RandomForestClassifier`.

1. **Change the Model:**
   Open `src/models/train_model.py`. If you want to use XGBoost, Logistic Regression, or a Regressor instead, import it and return it in `build_model()`.
2. **Update Hyperparameter Tuning (Optional):**
   If you swapped the model and want to use Optuna, open `src/models/tune_model.py` and update the `params` dictionary in the `objective()` function to search the correct hyperparameters for your new algorithm.
3. **Update Configs:**
   Open `configs/config.yaml`. Update the `model` section to reflect your new algorithm's default parameters.

## Step 5: Adjust Configuration and Registry

1. **Update Experiment Tracking:**
   In `configs/config.yaml`, change the `mlflow.experiment_name` from `churn_prediction` to the name of your project.
2. **Update Model Registry:**
   In the same file, update `registry.model_name` (e.g., `my_awesome_model`). Adjust the `accuracy_threshold` depending on the baseline performance of your specific problem.

## Step 6: Update Tests and Monitoring

1. **Fix Tests:**
   Open `tests/test_api_resilience.py` and `tests/test_batch_api.py`. Update the dummy JSON payloads (`"feature_0": 0.1`, etc.) to match your new `InferenceRequest` schema.
2. **Provide a Monitoring Baseline:**
   Evidently drift detection compares current data against a baseline. Once your first model is trained, the training data (`data/raw/dataset.csv`) naturally acts as the baseline reference in `configs/config.yaml`.

---

## 🚀 You're Ready for Production!

Once these steps are complete, your custom pipeline is fully integrated into the MLOps playbook!

Try running:
```bash
make run-all
make serve
```
