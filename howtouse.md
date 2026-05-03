# How to Use This Repo: Bring Your Own Dataset

This guide explains how to adapt the MLOps Playbook repository for your own machine learning project. The default repository uses a synthetic dataset. By following these steps, you can plug in your own dataset, update the pipelines, and get a production-ready system up and running quickly.

## Step 1: Replace the Dataset

The first step is bringing your own data into the system.

1. **Place your data:**
   Place your raw data (e.g., CSV files) in the `data/raw/` directory.

2. **Update the Configuration:**
   Open `configs/config.yaml` and update the `data.raw_path` to point to your new dataset.

   ```yaml
   data:
     raw_path: "data/raw/my_custom_dataset.csv"
     test_size: 0.2
     random_state: 42
   ```

3. **Update Data Ingestion:**
   If your data comes from a database, an S3 bucket, or an API, you will need to update `pipelines/data_ingestion.py` and `src/data/make_dataset.py`. Modify the code to pull from your specific data source instead of generating synthetic data.

## Step 2: Adapting the Schema

To ensure data quality, we use Pydantic for validation. You must update the schemas to match your dataset's columns and types.

1. **Update Data Validation Schema:**
   Open `src/data/validation.py`. Update the `DataSchema` Pydantic model to reflect the columns in your raw dataset. This runs during the ingestion pipeline to catch bad data early.

   ```python
   from pydantic import BaseModel, Field

   class DataSchema(BaseModel):
       # Example: replace these with your actual features
       age: int = Field(..., ge=0)
       income: float
       category: str
       target: int # or float for regression
   ```

2. **Update Inference Schema:**
   Open `src/inference/api.py`. Update the `PredictionRequest` Pydantic model. This defines the JSON payload your FastAPI endpoint will expect from clients. (Note: this usually does not include the `target` column).

   ```python
   class PredictionRequest(BaseModel):
       age: int
       income: float
       category: str
   ```

## Step 3: Feature Engineering Customization

Machine learning models require features to be preprocessed. You'll likely need to change the imputation, scaling, or encoding steps.

1. **Modify the Pipeline:**
   Open `src/features/build_features.py`. The `build_feature_pipeline()` function returns a scikit-learn `Pipeline` or `ColumnTransformer`. Update this to handle your specific numerical and categorical columns.

   ```python
   from sklearn.compose import ColumnTransformer
   from sklearn.pipeline import Pipeline
   from sklearn.preprocessing import StandardScaler, OneHotEncoder
   from sklearn.impute import SimpleImputer

   def build_feature_pipeline() -> Pipeline:
       numeric_features = ['age', 'income']
       categorical_features = ['category']

       numeric_transformer = Pipeline(steps=[
           ('imputer', SimpleImputer(strategy='median')),
           ('scaler', StandardScaler())
       ])

       categorical_transformer = Pipeline(steps=[
           ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
           ('onehot', OneHotEncoder(handle_unknown='ignore'))
       ])

       preprocessor = ColumnTransformer(
           transformers=[
               ('num', numeric_transformer, numeric_features),
               ('cat', categorical_transformer, categorical_features)
           ])

       return Pipeline(steps=[('preprocessor', preprocessor)])
   ```

## Step 4: Changing the Model Architecture

By default, the playbook might use a simple Random Forest. You can easily swap this out for XGBoost, LightGBM, or a simple PyTorch model.

1. **Update the Model Builder:**
   Open `src/models/train_model.py`. Modify the `build_model()` function to return your chosen model instance.

   ```python
   from xgboost import XGBClassifier

   def build_model(n_estimators: int = 100, max_depth: int = 3, **kwargs):
       # Replace the default model with your new one
       return XGBClassifier(
           n_estimators=n_estimators,
           max_depth=max_depth,
           use_label_encoder=False,
           eval_metric='logloss'
       )
   ```

2. **Update the Training Pipeline (if needed):**
   Open `pipelines/training_pipeline.py`. If your target column name is different from `"target"`, make sure to update the feature/target split logic:

   ```python
   # Change "target" to your actual target column name
   X = df.drop(columns=["your_target_column"])
   y = df["your_target_column"]
   ```

3. **Update Hyperparameter Tuning (Optional):**
   If you enabled Optuna in `configs/config.yaml`, update the search space in `src/models/tune_model.py` to match the hyperparameter arguments of your new model.

## Step 5: Run the End-to-End Pipeline

Once these changes are made, run the standard Make commands to test your new implementation:

```bash
# Run ingestion (and validation)
python pipelines/data_ingestion.py

# Run training (and tracking)
python pipelines/training_pipeline.py

# Serve the model
make serve
```

Send a test request to your new API endpoint at `http://localhost:8000/predict` using the schema you defined in Step 2!