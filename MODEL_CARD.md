# Model Card — [Model Name]

> Fill this in after training. Commit one MODEL_CARD.md per registered model version.
> Reference: [Mitchell et al. 2019](https://arxiv.org/abs/1810.03993)

---

## Model Details

| Field | Value |
|---|---|
| Model type | RandomForestClassifier (sklearn) |
| Version | 1.0.0 |
| Training date | YYYY-MM-DD |
| Framework | scikit-learn |
| MLflow run ID | (paste run ID from mlflow ui) |

## Intended Use

- **Primary use:** Binary classification — predicting customer churn
- **Intended users:** Data scientists, ML engineers
- **Out-of-scope uses:** Real-time fraud detection, medical decisions, any high-stakes automated decision-making without human review

## Training Data

| Field | Value |
|---|---|
| Dataset | Synthetic churn dataset (sklearn `make_classification`) |
| Size | 1,000 samples |
| Features | 10 numeric features (5 informative, 2 redundant) |
| Target | Binary (0 = retained, 1 = churned) |
| Class balance | ~50/50 (configurable) |
| Data version | See `data/raw/.gitkeep` — use DVC in production |

## Evaluation Metrics

| Metric | Value |
|---|---|
| Accuracy | |
| Precision | |
| Recall | |
| F1 | |
| ROC-AUC | |

> Fill in after running `make train`. Values logged to MLflow.

## Ethical Considerations

- This model is trained on **synthetic data** and should not be used for real decisions without retraining on validated real-world data
- No demographic features are present in the training data
- Feature importance should be reviewed before production deployment to check for proxy discrimination

## Caveats and Recommendations

- Retrain on real customer data before any production use
- Establish a drift detection baseline using `monitoring/drift_detection.py`
- Set a performance threshold below which the model triggers a retraining alert
- Validate that training distribution matches inference distribution (train/serve skew)
