"""Opt-in repeatability check using the live cluster and live decision model."""

import os

import pytest

from openops.decision import OpenAIDecisionProvider
from openops.kubernetes_adapter import build_live_collector_suite
from openops.models import InvestigationStatus
from openops.runtime import run_investigation
from tests.helpers import objective

pytestmark = pytest.mark.live_model


def test_three_live_runs_are_semantically_equivalent() -> None:
    if os.environ.get("OPENOPS_LIVE_MODEL") != "1" or not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("set OPENOPS_LIVE_MODEL=1 and OPENAI_API_KEY to run paid live verification")
    outcomes = []
    for _ in range(3):
        target = objective()
        outcomes.append(
            run_investigation(
                target,
                build_live_collector_suite(target),
                OpenAIDecisionProvider(),
            )
        )
    for outcome in outcomes:
        assert outcome.state.status is InvestigationStatus.COMPLETED
        assert outcome.state.decision is not None
        assert outcome.state.decision.confidence.value == "high"
        cause = outcome.state.decision.cause.lower()
        assert "/ready" in cause
        assert "404" in cause
        cited = {
            item.id: item.observation
            for item in outcome.state.evidence
            if item.id in outcome.state.decision.evidence_ids
        }
        text = "\n".join(cited.values())
        assert "path /ready on port 80" in text
        assert "Ready condition is False" in text
        assert "HTTP status 404" in text
