"""Tests for the one-call structured OpenAI provider boundary."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from openops.decision import OpenAIDecisionProvider, validate_diagnosis
from openops.models import Confidence, FinalDiagnosis
from openops.normalizer import normalize_evidence
from tests.helpers import fixture_result, objective

pytestmark = pytest.mark.unit


class _Responses:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_parsed=FinalDiagnosis(
                cause=(
                    "The /ready readiness probe returns HTTP 404, so Kubernetes keeps the Pod "
                    "unready."
                ),
                confidence=Confidence.HIGH,
                evidence_ids=("evidence-002", "evidence-003", "evidence-005"),
                alternatives=(),
                recommendation="Use the successful / endpoint; do not apply it automatically.",
            )
        )


def test_openai_provider_makes_one_bounded_structured_call() -> None:
    responses = _Responses()
    api = SimpleNamespace(responses=responses)
    target = objective()
    evidence = tuple(
        normalize_evidence(
            target,
            [fixture_result(name) for name in ("deployment", "pods", "events")],
        )
    )
    provider = OpenAIDecisionProvider(client=api, model="test-model")
    candidate = provider.diagnose(target, evidence)
    diagnosis = validate_diagnosis(candidate, list(evidence))

    assert diagnosis.confidence.value == "high"
    assert provider.call_count == 1
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call["model"] == "test-model"
    assert call["text_format"] is FinalDiagnosis
    assert call["max_output_tokens"] == 1000
    context = json.loads(call["input"][1]["content"])
    serialized = json.dumps(context)
    assert "raw_reference" not in serialized
    assert "Readiness probe failed:" not in serialized
    assert set(context) == {"objective", "evidence"}
