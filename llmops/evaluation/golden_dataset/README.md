# llmops/evaluation/golden_dataset/README.md
#
# Golden Dataset — LLM Evaluation Reference Corpus

## What is the Golden Dataset?

The golden dataset is a curated, version-controlled set of (prompt, expected_response)
pairs that represent the highest-quality reference answers for the tasks this LLM
is fine-tuned on.

Unlike benchmark YAML files (which focus on a single dimension, e.g. commonsense QA),
the golden dataset is domain-specific and maintained by the model's subject-matter
experts.

## Directory Structure

```
llmops/evaluation/golden_dataset/
  README.md                  ← this file
  <domain>/
    pairs.jsonl              ← one JSON object per line: {"prompt": "...", "reference": "..."}
    metadata.yaml            ← domain, contributor, last_reviewed, dvc_hash
```

## Adding New Examples

1. Edit (or create) `pairs.jsonl` in the relevant domain sub-directory.
2. Run `dvc add llmops/evaluation/golden_dataset/<domain>/pairs.jsonl` to
   version the dataset.
3. Update `metadata.yaml` with the new DVC hash and review date.
4. Open a PR with the label `golden-dataset-update`.

## Quality Gates

- Minimum 50 examples per domain before CI benchmarks use the golden dataset.
- Each example must have a unique, unambiguous `reference` output.
- Periodic review: subject-matter experts sign off on the golden dataset every
  quarter via the approval checklist in `policy/model-approval/`.

## Using in Evaluation

Pass the golden dataset directory to the evaluation harness:

```bash
python llmops/evaluation/harness.py \\
  --model-name    my-llm \\
  --model-version 3 \\
  --endpoint-url  https://my-endpoint/predict \\
  --golden-dataset-dir llmops/evaluation/golden_dataset/
```

The harness automatically discovers all `pairs.jsonl` files in sub-directories.
