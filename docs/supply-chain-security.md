# MLOps Supply-Chain Security

## Release requirements

1. Dependencies are resolved from lockfiles with hashes.
2. GitHub Actions are pinned to immutable commit SHAs in high-trust workflows.
3. Container images are built once and deployed by digest.
4. An SBOM is generated for every image and retained with the release.
5. Images and provenance attestations are signed and verified before deployment.
6. The release records source commit, builder, inputs, dependency lock hash,
   image digest, model artifact digest, and verification result.

The reusable scan in
`ci/github-actions/_shared/reusable-mlops-scan.yml` is a baseline. It does not
replace SBOM generation, signing, or provenance verification.

## Required CI evidence

The release artifact should contain:

- dependency audit output,
- secret scan output,
- IaC scan output,
- SBOM,
- image digest,
- signature verification result,
- SLSA-compatible build provenance,
- model artifact hash,
- deployment manifest rendered with immutable references.

## Deployment rule

Mutable tags such as `latest` and `production-latest` are prohibited in
production manifests. The production overlay uses a digest replacement marker;
the deployment workflow must replace it with a verified release digest before
applying the rendered manifest.
