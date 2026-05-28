# PII Model Promotion Checklist
#
# PURPOSE:
#   Complete this checklist before promoting any model to Production if the
#   training data contained Personally Identifiable Information (PII) or
#   data classified as 'confidential' or 'restricted'.
#
# HOW TO USE:
#   1. Copy this checklist into the model's Pull Request description.
#   2. Check each item. If an item does not apply, note why.
#   3. A Data Protection Officer (DPO) or designated data steward must
#      review and approve the PR before merging.
#
# LEGAL NOTE:
#   PII handling requirements are governed by GDPR (EU), CCPA (California),
#   and internal data governance policy. Failure to complete this checklist
#   can result in a mandatory incident report to the DPO.

## Model Details

- **Model name (MLflow):** `_____`
- **Model version:** `_____`
- **MLflow run ID:** `_____`
- **DVC data hash:** `_____`
- **Completed by:** `_____`
- **Date:** `_____`

---

## Checklist

### 1. Data Approval
- [ ] A Data Protection Officer (DPO) or data steward has approved use of this PII dataset for ML training.
      > _Approval ticket / email reference: `_____`_

- [ ] A lawful basis for processing under GDPR Article 6 has been identified and documented.
      > _Lawful basis (e.g., legitimate interest, consent, contract): `_____`_

### 2. Data Minimisation
- [ ] Only the columns strictly necessary for the model task are included in the training dataset.
      > _List of included PII columns (if any): `_____`_

- [ ] All columns not required for prediction have been dropped before the dataset was versioned in DVC.

### 3. Pseudonymisation / Anonymisation
- [ ] All direct identifiers (name, email, phone, SSN, IP address, user ID) have been replaced with
      opaque tokens or removed before training.
      > _Pseudonymisation method used: `_____`_

- [ ] The tokenisation mapping is stored separately with restricted access (not in the ML artifact store).
      > _Storage location of mapping: `_____`_

### 4. MLflow Hygiene
- [ ] No PII values are logged as MLflow parameters, metrics, or tags.
- [ ] No PII values appear in artifact filenames or paths.
- [ ] The model artifact (pkl/pt/onnx) has been checked to confirm it does not memorise
      individual training examples (e.g., via membership inference test).

### 5. Model Card
- [ ] The model card (or MLflow model description) states:
      - The data sensitivity level (`confidential` or `restricted`).
      - What PII columns were present in training data (even if pseudonymised).
      - The DPO approval reference.

### 6. Deletion Procedure
- [ ] A documented procedure exists to retrain or remove the model if a data subject
      submits a right-to-erasure (GDPR Article 17) request for their data.
      > _Erasure procedure location: `_____`_

- [ ] The DVC dataset `.dvc` metadata includes `contains_pii: true` and `data_owner` fields.

### 7. Access Control
- [ ] The Production model is accessible only to authorised service accounts.
- [ ] The training dataset in the DVC remote is stored in an access-controlled bucket
      with audit logging enabled.

### 8. Data Retention
- [ ] The dataset retention period is set in the DVC `.dvc` metadata (`retention_days` field).
- [ ] A scheduled cleanup job is configured to delete the dataset after the retention period.

---

## Approvals

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Model author | | | |
| Data Protection Officer | | | |
| ML Platform approver | | | |
