# Student Model Configuration Directory

Place student model architecture YAML files here.  Each file defines the smaller
model architecture that will learn to mimic a teacher model via knowledge distillation.

## File Format

```yaml
# student_configs/my-small-classifier.yaml

# HuggingFace model ID or local path for the student architecture
architecture: distilbert-base-uncased

# Tokenizer to use (can differ from architecture name)
tokenizer: distilbert-base-uncased

# Dataset column names
text_column: text
label_column: label

# Optional: override distillation hyperparameters per student config
# temperature: 4.0
# alpha: 0.7
```

## Naming Convention

Name student config files after the target use case:
- `small-classifier.yaml`     — DistilBERT-based text classifier
- `tiny-sentiment.yaml`       — TinyBERT-based sentiment model
- `minibert-qa.yaml`          — MiniLM for question answering

## Rule

The teacher model must be in **Production** stage in the MLflow Model Registry
before distillation is initiated.  The distillation loss combines soft KL-divergence
targets (from teacher logits) with hard cross-entropy labels.
