"""Tests for deterministic bounded evidence normalization."""

import pytest

from openops.normalizer import NormalizationError, normalize_evidence
from tests.helpers import fixture_result, objective

pytestmark = pytest.mark.unit


def test_fixture_normalization_is_stable_and_provenanced() -> None:
    results = [fixture_result(name) for name in ("deployment", "pods", "events")]
    first = normalize_evidence(objective(), results)
    second = normalize_evidence(objective(), results)
    assert first == second
    assert [item.id for item in first] == [f"evidence-{number:03d}" for number in range(1, 6)]
    assert all(item.raw_reference.startswith("tool-result:tool-") for item in first)
    observations = "\n".join(item.observation for item in first)
    assert "path /ready on port 80" in observations
    assert "Ready condition is False" in observations
    assert "HTTP status 404" in observations
    assert "Readiness probe failed:" not in observations


def test_normalization_fails_closed_at_evidence_limit() -> None:
    results = [fixture_result(name) for name in ("deployment", "pods", "events")]
    with pytest.raises(NormalizationError):
        normalize_evidence(objective(), results, limit=4)
