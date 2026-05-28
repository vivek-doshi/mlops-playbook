# Data Governance Policy

All datasets used in this MLOps platform must be classified, versioned, and handled
according to the rules in this document.

---

## 1. Data Classification

Every dataset must be tagged with a classification level before use in training.

| Classification | Description | Storage requirements | DVC tagging |
|---------------|-------------|---------------------|-------------|
| `public` | No sensitive data; publicly available | Standard S3/GCS/Azure Blob | `classification: public` |
| `internal` | Business data, no PII | Encrypted at rest, private bucket | `classification: internal` |
| `confidential` | PII, financial, health data | Encrypted at rest + in transit, restricted access, audit log | `classification: confidential` |
| `restricted` | Regulated data (GDPR, HIPAA, PCI) | All of confidential + additional DLP controls, no ML training without DPA | `classification: restricted` |

### Tagging datasets in DVC

Add classification metadata to your DVC file:

```yaml
# data/customer_features.parquet.dvc
outs:
  - md5: abc123...
    path: data/customer_features.parquet
    meta:
      classification: confidential
      contains_pii: true
      data_owner: data-platform-team@example.com
      retention_days: 365
```

---

## 2. PII Handling Rules

If a dataset contains Personally Identifiable Information (PII):

1. **Explicit approval** — A Data Protection Officer (DPO) or designated data steward
   must approve the use of PII data in ML training before the dataset is added to DVC.

2. **Minimum necessary** — Extract only the columns required for the model.
   Never store full PII datasets in the ML artifact store.

3. **Pseudonymisation** — Replace direct identifiers (name, email, phone, SSN) with
   opaque tokens before training. The tokenisation mapping must be stored separately
   with restricted access.

4. **No PII in MLflow** — Do not log PII values as MLflow parameters, tags, or
   artifact filenames.

5. **Deletion on request** — Datasets that may contain PII must support deletion
   on individual data subject request (GDPR right to erasure). Document the dataset
   identifier and storage location in the DVC metadata.

See `policy/data-governance/pii-model-checklist.md` for the checklist that must be
completed before promoting a PII-trained model to Production.

---

## 3. Data Retention

| Classification | Default retention | Action on expiry |
|---------------|-------------------|-----------------|
| public | 2 years | Archive to cold storage |
| internal | 1 year | Delete |
| confidential | 1 year | Delete with audit log |
| restricted | Per regulation (GDPR: as long as lawful basis exists) | Delete with DPO sign-off |

The retention period in days should be set in the DVC metadata `retention_days` field.
A scheduled script in `devops-playbook/scripts/data-retention-cleanup.py` checks
for expired datasets and creates deletion requests.

---

## 4. Feature Store and Training-Serving Skew

Derived features that are computed from confidential or restricted data carry the
same classification as the source data. This applies to features stored in the
Vertex AI Feature Store or in Parquet snapshots tracked by DVC.

See `docs/guides/feature-store-patterns.md` for guidance on maintaining feature
lineage across training and serving without exposing sensitive raw data.

---

## 5. Cross-Border Data Transfer

Training data must not be transferred across regional boundaries when the data
classification is `restricted`. Configure DVC remotes and cloud storage buckets
to remain within the required region.

```bash
# Example: configure DVC to use a region-locked Azure Blob remote.
dvc remote add -d azure-eu azure://my-bucket-eu/dvc
dvc remote modify azure-eu account_name my_storage_account
# The storage account itself is configured to allow access only from eu-west-1.
```

---

## Related

- `policy/data-governance/pii-model-checklist.md` — PII model promotion checklist
- `docs/guides/feature-store-patterns.md` — feature classification in feature store
- `dvc/remote-storage/README.md` — DVC remote configuration
- `devops-playbook/policy/kyverno/` — Kubernetes-level data isolation policies
