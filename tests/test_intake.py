"""Tests for fixed validation before external calls."""

import pytest

from openops.intake import IntakeError, parse_duration, validate_intake

pytestmark = pytest.mark.unit


def test_exact_intake_is_accepted() -> None:
    objective = validate_intake(
        cluster_context="openops-reader@kind-openops-lab",
        namespace="openops-lab",
        workload_kind="Deployment",
        workload_name="readiness-demo",
        symptom="Pod is Running but not Ready",
        time_window="30m",
    )
    assert objective.time_window_seconds == 1800


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("cluster_context", "kind-openops-lab"),
        ("namespace", "default"),
        ("workload_kind", "Pod"),
        ("workload_name", "another-deployment"),
    ],
)
def test_any_other_target_is_rejected(field: str, value: str) -> None:
    arguments = {
        "cluster_context": "openops-reader@kind-openops-lab",
        "namespace": "openops-lab",
        "workload_kind": "Deployment",
        "workload_name": "readiness-demo",
        "symptom": "Pod is Running but not Ready",
    }
    arguments[field] = value
    with pytest.raises(IntakeError):
        validate_intake(**arguments)


@pytest.mark.parametrize(("value", "seconds"), [("30s", 30), ("30m", 1800), ("1h", 3600)])
def test_bounded_duration(value: str, seconds: int) -> None:
    assert parse_duration(value) == seconds


@pytest.mark.parametrize("value", ["0m", "61m", "2h", "30", "-1m"])
def test_invalid_duration_is_rejected(value: str) -> None:
    with pytest.raises(IntakeError):
        parse_duration(value)
