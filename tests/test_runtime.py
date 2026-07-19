"""Deterministic end-to-end investigation tests."""

from __future__ import annotations

import pytest

from openops.decision import (
    DiagnosisValidationError,
    FakeDecisionProvider,
    ModelProviderError,
    model_context,
    validate_diagnosis,
)
from openops.models import InvestigationStatus
from openops.runtime import run_investigation
from tests.helpers import FixtureCollectors, NoEvidenceCollectors, objective

pytestmark = pytest.mark.unit


def test_complete_flow_uses_fixed_order_one_model_call_and_cited_report() -> None:
    collectors = FixtureCollectors()
    provider = FakeDecisionProvider()
    outcome = run_investigation(objective(), collectors, provider)

    assert outcome.state.status is InvestigationStatus.COMPLETED
    assert collectors.calls == ["deployment", "pods", "events"]
    assert len(outcome.state.tool_results) == 3
    assert provider.call_count == 1
    assert outcome.state.decision is not None
    assert outcome.state.decision.evidence_ids == (
        "evidence-002",
        "evidence-003",
        "evidence-005",
    )
    assert outcome.report is not None
    assert "HTTP readiness probe requests /ready" in outcome.report
    assert "evidence-005: Kubernetes reported" in outcome.report


def test_model_context_contains_only_objective_and_normalized_visible_evidence() -> None:
    provider = FakeDecisionProvider()
    outcome = run_investigation(objective(), FixtureCollectors(), provider)
    payload = model_context(outcome.state.objective, tuple(outcome.state.evidence))
    serialized = str(payload)
    assert set(payload) == {"objective", "evidence"}
    assert "raw_reference" not in serialized
    assert "ToolResult" not in serialized
    assert "Readiness probe failed:" not in serialized
    assert "token" not in serialized.lower()


def test_collector_exception_is_stored_and_remaining_collectors_are_attempted() -> None:
    collectors = FixtureCollectors(fail_deployment=True)
    outcome = run_investigation(objective(), collectors, FakeDecisionProvider())
    assert collectors.calls == ["deployment", "pods", "events"]
    assert outcome.state.tool_results[0].status.value == "failure"
    assert outcome.state.tool_results[0].error_message == (
        "kubernetes_deployment failed (execution_error)."
    )


class _InvalidProvider:
    def __init__(self, candidate: object) -> None:
        self.candidate = candidate
        self.calls = 0

    def diagnose(self, objective_value: object, evidence_value: object) -> object:
        del objective_value, evidence_value
        self.calls += 1
        return self.candidate


@pytest.mark.parametrize(
    "candidate",
    [
        {},
        {
            "cause": "Unsupported",
            "confidence": "high",
            "evidence_ids": [],
            "alternatives": [],
            "recommendation": "Do nothing",
        },
        {
            "cause": "Unsupported",
            "confidence": "high",
            "evidence_ids": ["evidence-999"],
            "alternatives": [],
            "recommendation": "Do nothing",
        },
        {
            "cause": "Unsupported",
            "confidence": "high",
            "evidence_ids": ["evidence-001", "evidence-001"],
            "alternatives": [],
            "recommendation": "Do nothing",
        },
    ],
)
def test_invalid_diagnosis_fails_closed_without_report(candidate: object) -> None:
    provider = _InvalidProvider(candidate)
    outcome = run_investigation(objective(), FixtureCollectors(), provider)
    assert outcome.state.status is InvestigationStatus.FAILED
    assert outcome.state.failure is not None
    assert outcome.state.failure.stage.value == "validation"
    assert outcome.state.decision is None
    assert outcome.report is None
    assert provider.calls == 1


class _FailingProvider:
    def diagnose(self, objective_value: object, evidence_value: object) -> object:
        del objective_value, evidence_value
        raise ModelProviderError("secret provider detail")


def test_model_failure_is_not_retried_or_rendered() -> None:
    outcome = run_investigation(objective(), FixtureCollectors(), _FailingProvider())
    assert outcome.state.status is InvestigationStatus.FAILED
    assert outcome.state.failure is not None
    assert outcome.state.failure.stage.value == "model"
    assert outcome.report is None


def test_no_evidence_fails_before_model_after_all_three_attempts() -> None:
    collectors = NoEvidenceCollectors()
    provider = FakeDecisionProvider()
    outcome = run_investigation(objective(), collectors, provider)
    assert collectors.calls == ["deployment", "pods", "events"]
    assert len(outcome.state.tool_results) == 3
    assert outcome.state.status is InvestigationStatus.FAILED
    assert outcome.state.phase.value == "finished"
    assert outcome.state.failure is not None
    assert outcome.state.failure.stage.value == "collection"
    assert provider.call_count == 0
    assert outcome.report is None


def test_validator_rejects_unknown_evidence_independently() -> None:
    evidence = run_investigation(
        objective(), FixtureCollectors(), FakeDecisionProvider()
    ).state.evidence
    with pytest.raises(DiagnosisValidationError):
        validate_diagnosis(
            {
                "cause": "Unsupported",
                "confidence": "high",
                "evidence_ids": ["evidence-999"],
                "alternatives": [],
                "recommendation": "Do nothing",
            },
            evidence,
        )
