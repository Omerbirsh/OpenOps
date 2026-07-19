"""Opt-in live-cluster verification using the deterministic fake provider."""

import os
from pathlib import Path

import pytest

from openops.cli import main
from openops.decision import FakeDecisionProvider
from openops.kubernetes_adapter import build_live_collector_suite
from openops.models import InvestigationStatus
from openops.runtime import run_investigation
from tests.helpers import objective

pytestmark = pytest.mark.live_cluster


def test_live_broken_readiness_collection_and_fake_decision() -> None:
    if os.environ.get("OPENOPS_LIVE_CLUSTER") != "1":
        pytest.skip("set OPENOPS_LIVE_CLUSTER=1 after creating and faulting the disposable lab")
    target = objective()
    outcome = run_investigation(target, build_live_collector_suite(target), FakeDecisionProvider())
    assert outcome.state.status is InvestigationStatus.COMPLETED
    assert outcome.state.decision is not None
    assert outcome.state.decision.confidence.value == "high"
    observations = "\n".join(item.observation for item in outcome.state.evidence)
    assert "path /ready on port 80" in observations
    assert "Ready condition is False" in observations
    assert "HTTP status 404" in observations


def test_live_cli_collects_real_evidence_and_writes_sanitized_trace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    if os.environ.get("OPENOPS_LIVE_CLUSTER") != "1":
        pytest.skip("set OPENOPS_LIVE_CLUSTER=1 after creating and faulting the disposable lab")
    target = objective()
    trace = tmp_path / "live-trace.json"
    exit_code = main(
        [
            "investigate",
            "--cluster-context",
            target.cluster_context,
            "--namespace",
            target.namespace,
            "--workload-kind",
            target.workload_kind,
            "--workload-name",
            target.workload_name,
            "--symptom",
            target.symptom,
            "--trace-file",
            str(trace),
        ],
        collectors=build_live_collector_suite(target),
        provider=FakeDecisionProvider(),
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Confidence: high" in captured.out
    assert captured.err == ""
    content = trace.read_text(encoding="utf-8")
    assert "HTTP status 404" in content
    assert "raw_reference" not in content
    assert "Readiness probe failed:" not in content
