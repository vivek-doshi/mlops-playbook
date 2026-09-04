# Compatibility Contract

---
**Owner**: @mlops-team
**Last Reviewed**: 2026-09-04
**Source of Truth**: docs/topology/INTEGRATION-BRIDGE.md
**Depends On**: external devops-playbook repository
---

## Platform Manifest Requirements

The MLOps repository requires the platform repository to publish the following manifest:

```yaml
# Platform Manifest (cicd-reference/manifest.yaml)
platform:
  version: "1.2.0"
  components:
    gpu-cluster:
      version: "v1.2.0"
      required: true
    base-kubernetes:
      version: "v1.28.0"
      required: true
    secrets-management:
      version: "v1.0.0"
      required: true
    oidc-federation:
      version: "v1.1.0"
      required: true
    policy-controls:
      version: "v1.0.0"
      required: true
    observability-baseline:
      version: "v1.0.0"
      required: true

compatibility:
  min-platform-version: "1.2.0"
  max-platform-version: "1.3.0"
  required-features:
    - gpu-provisioning
    - k8s-primitives
    - secrets-handling
    - oidc-auth
    - policy-enforcement
    - observability-baseline
```

## Compatibility Requirements

### Minimum Platform Version

The MLOps repository requires a minimum platform version of **1.2.0**. This version includes:

- **GPU Provisioning**: GPU cluster provisioning and workload scheduling
- **K8s Primitives**: Base Kubernetes primitives and manifests
- **Secrets Handling**: Secrets management and credential handling
- **OIDC Auth**: Identity federation and authentication
- **Policy Enforcement**: Policy enforcement and governance
- **Observability Baseline**: Monitoring and alerting infrastructure

### Maximum Platform Version

The MLOps repository supports a maximum platform version of **1.3.0**. This version includes:

- **GPU Provisioning**: GPU cluster provisioning and workload scheduling
- **K8s Primitives**: Base Kubernetes primitives and manifests
- **Secrets Handling**: Secrets management and credential handling
- **OIDC Auth**: Identity federation and authentication
- **Policy Enforcement**: Policy enforcement and governance
- **Observability Baseline**: Monitoring and alerting infrastructure

### Required Features

The MLOps repository requires the following platform features:

1. **GPU Provisioning**: GPU cluster provisioning and workload scheduling
2. **K8s Primitives**: Base Kubernetes primitives and manifests
3. **Secrets Handling**: Secrets management and credential handling
4. **OIDC Auth**: Identity federation and authentication
5. **Policy Enforcement**: Policy enforcement and governance
6. **Observability Baseline**: Monitoring and alerting infrastructure

## Compatibility Contract Details

### GPU Cluster Compatibility

**Requirements**:
- Minimum version: v1.2.0
- Required features: GPU provisioning, workload scheduling
- Configuration input: `cluster-config.yaml`

**Usage in MLOps**:
- Training, distributed training, batch inference
- Resource allocation and workload scheduling

**Compatibility Matrix**:

| Platform Version | Compatible | Notes |
|-----------------|------------|-------|
| 1.1.0 | ❌ | Missing GPU provisioning |
| 1.2.0 | ✅ | Full compatibility |
| 1.2.5 | ✅ | Full compatibility |
| 1.3.0 | ✅ | Full compatibility |
| 1.3.1 | ⚠️ | May have breaking changes |

### Base Kubernetes Compatibility

**Requirements**:
- Minimum version: v1.28.0
- Required features: K8s primitives, admission, runtime, storage
- Configuration input: `k8s-base.yaml`

**Usage in MLOps**:
- Model serving, deployment, CI/CD
- Kubernetes workload execution

**Compatibility Matrix**:

| Platform Version | Compatible | Notes |
|-----------------|------------|-------|
| 1.27.0 | ❌ | Missing K8s primitives |
| 1.28.0 | ✅ | Full compatibility |
| 1.28.5 | ✅ | Full compatibility |
| 1.29.0 | ⚠️ | May have breaking changes |

### Secrets Management Compatibility

**Requirements**:
- Minimum version: v1.0.0
- Required features: Secrets, configmaps
- Configuration input: `secrets-config.yaml`

**Usage in MLOps**:
- Model registry, serving, monitoring
- Credential handling and security

**Compatibility Matrix**:

| Platform Version | Compatible | Notes |
|-----------------|------------|-------|
| 0.9.0 | ❌ | Missing secrets handling |
| 1.0.0 | ✅ | Full compatibility |
| 1.0.5 | ✅ | Full compatibility |
| 1.1.0 | ⚠️ | May have breaking changes |

### OIDC Federation Compatibility

**Requirements**:
- Minimum version: v1.1.0
- Required features: OIDC, authentication
- Configuration input: `oidc-config.yaml`

**Usage in MLOps**:
- CI/CD workflows, model promotion
- Identity federation and authentication

**Compatibility Matrix**:

| Platform Version | Compatible | Notes |
|-----------------|------------|-------|
| 1.0.0 | ❌ | Missing OIDC auth |
| 1.1.0 | ✅ | Full compatibility |
| 1.1.5 | ✅ | Full compatibility |
| 1.2.0 | ⚠️ | May have breaking changes |

### Policy Controls Compatibility

**Requirements**:
- Minimum version: v1.0.0
- Required features: Policies, admission, governance
- Configuration input: `policy-config.yaml`

**Usage in MLOps**:
- Model approval, data governance, fairness
- Policy enforcement and governance

**Compatibility Matrix**:

| Platform Version | Compatible | Notes |
|-----------------|------------|-------|
| 0.9.0 | ❌ | Missing policy enforcement |
| 1.0.0 | ✅ | Full compatibility |
| 1.0.5 | ✅ | Full compatibility |
| 1.1.0 | ⚠️ | May have breaking changes |

### Observability Baseline Compatibility

**Requirements**:
- Minimum version: v1.0.0
- Required features: Monitoring, alerting, dashboards
- Configuration input: `observability-config.yaml`

**Usage in MLOps**:
- Monitoring, FinOps, drift detection
- Monitoring and alerting infrastructure

**Compatibility Matrix**:

| Platform Version | Compatible | Notes |
|-----------------|------------|-------|
| 0.9.0 | ❌ | Missing observability baseline |
| 1.0.0 | ✅ | Full compatibility |
| 1.0.5 | ✅ | Full compatibility |
| 1.1.0 | ⚠️ | May have breaking changes |

## CI Check for Platform Manifest

### Platform Compatibility Check Workflow

```yaml
# .github/workflows/platform-compatibility.yml
name: Platform Compatibility Check

on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly
  pull_request:
    branches: [main, develop]

jobs:
  check-platform-manifest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download platform manifest
        run: |
          # Download platform manifest from cicd-reference
          git clone https://github.com/platform/cicd-reference.git
          
      - name: Validate platform version
        run: |
          # Check platform version compatibility
          platform_version=$(cat cicd-reference/manifest.yaml | grep version)
          min_version=$(cat .cicd-reference/manifest.yaml | grep min-platform-version)
          
          if [ "$platform_version" < "$min_version" ]; then
            echo "❌ Platform version $platform_version is incompatible"
            exit 1
          fi
      
      - name: Check required features
        run: |
          # Verify all required features are present
          required_features=$(cat .cicd-reference/manifest.yaml | grep required-features)
          
          for feature in $required_features; do
            if [ ! -f "$feature" ]; then
              echo "❌ Missing required feature: $feature"
              exit 1
            fi
          done
      
      - name: Validate component compatibility
        run: |
          # Check each component's compatibility
          components=(
            "gpu-cluster"
            "base-kubernetes"
            "secrets-management"
            "oidc-federation"
            "policy-controls"
            "observability-baseline"
          )
          
          for component in "${components[@]}"; do
            component_version=$(cat cicd-reference/manifest.yaml | grep "$component: version")
            min_version=$(cat .cicd-reference/manifest.yaml | grep min-platform-version)
            
            if [ "$component_version" < "$min_version" ]; then
              echo "❌ Component $component version $component_version is incompatible"
              exit 1
            fi
          done
```

## Compatibility Enforcement

### CI Enforcement

The repository includes CI checks to validate platform manifest compatibility:

1. **Platform Version Check**: Validates platform version meets minimum requirement
2. **Required Features Check**: Verifies all required features are present
3. **Component Compatibility Check**: Validates each component's compatibility

### Monthly Check

The repository performs monthly compatibility checks to ensure:

1. **Platform Version**: Platform version is compatible with minimum requirement
2. **Required Features**: All required features are present and functional
3. **Component Compatibility**: Each component's version is compatible

### PR-Based Check

The repository validates compatibility on every structural PR to ensure:

1. **Platform Version**: Platform version is compatible with minimum requirement
2. **Required Features**: All required features are present and functional
3. **Component Compatibility**: Each component's version is compatible

## Compatibility Best Practices

### 1. Regular Updates

- Review compatibility contract on every structural PR
- Run monthly compatibility checks
- Update platform manifest as needed
- Test affected workflows with new compatibility

### 2. Clear Documentation

- Maintain up-to-date compatibility contract documentation
- Document all platform primitives and versions
- Keep configuration inputs documented
- Document compatibility matrix and notes

### 3. Enforceable Interface

- Turn "not islands" from a principle into an enforceable interface
- Use CI checks to validate compatibility contract
- Automate compatibility validation
- Make compatibility contract explicit and enforceable

### 4. Regular Validation

- Validate compatibility on every structural PR
- Run monthly compatibility checks
- Validate component compatibility
- Ensure compatibility contract is enforceable

## Related Resources

- [Integration Bridge](INTEGRATION-BRIDGE.md) - Repository responsibility map and integration contract
- [Dependency Matrix](DEPENDENCY-MATRIX.md) - Executable dependency matrix
- [Control Planes](CONTROL-PLANES.md) - Control plane and data plane architecture
- [Architecture Decision Guide](ARCHITECTURE_DECISION_GUIDE.md) - Architectural decisions and patterns
- [Golden Paths](docs/golden-paths/) - End-to-end workflows and implementation guides
- [CI Workflows](ci/github-actions/) - Training, evaluation, and deployment workflows
- [CD Workflows](cd/argo/pipelines/) - Production workflow DAGs
- [Infrastructure](terraform/) - Cloud-specific ML infrastructure starter configurations
