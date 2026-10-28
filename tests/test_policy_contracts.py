from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def test_approval_registry_has_a_stable_schema() -> None:
    document = yaml.safe_load((ROOT / "policy/model-approval/approved-versions.yaml").read_text())

    assert isinstance(document, dict)
    assert isinstance(document.get("approvals"), list)


def test_production_slo_defaults_are_defined() -> None:
    document = yaml.safe_load((ROOT / "monitoring/slos/_defaults.yaml").read_text())

    defaults = document["slo_defaults"]
    assert defaults["availability"]["target"] >= 0.99
    assert defaults["latency_p99_ms"]["threshold"] > 0
    assert defaults["error_rate_pct"]["threshold"] > 0
