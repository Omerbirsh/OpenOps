"""Tests for the real CLI boundary with deterministic injected adapters."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openops.cli import main
from openops.decision import FakeDecisionProvider
from tests.helpers import FixtureCollectors

pytestmark = pytest.mark.unit

VALID_ARGS = [
    "investigate",
    "--cluster-context",
    "openops-reader@kind-openops-lab",
    "--namespace",
    "openops-lab",
    "--workload-kind",
    "Deployment",
    "--workload-name",
    "readiness-demo",
    "--symptom",
    "Pod is Running but not Ready",
]


def test_cli_runs_complete_fixture_backed_flow(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(VALID_ARGS, collectors=FixtureCollectors(), provider=FakeDecisionProvider()) == 0
    captured = capsys.readouterr()
    assert "OpenOps investigation report" in captured.out
    assert "Confidence: high" in captured.out
    assert captured.err == ""


def test_cli_writes_only_sanitized_trace(tmp_path: Path) -> None:
    path = tmp_path / "trace.json"
    assert (
        main(
            [*VALID_ARGS, "--trace-file", str(path)],
            collectors=FixtureCollectors(),
            provider=FakeDecisionProvider(),
        )
        == 0
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    serialized = json.dumps(payload)
    assert payload["status"] == "completed"
    assert "raw_reference" not in serialized
    assert "Readiness probe failed:" not in serialized
    assert "data" not in payload["collector_summaries"][0]


def test_invalid_intake_stops_before_collectors(capsys: pytest.CaptureFixture[str]) -> None:
    collectors = FixtureCollectors()
    arguments = VALID_ARGS.copy()
    arguments[arguments.index("openops-lab")] = "default"
    assert main(arguments, collectors=collectors, provider=FakeDecisionProvider()) == 2
    assert collectors.calls == []
    assert "namespace must equal" in capsys.readouterr().err


def test_no_command_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "input error" in capsys.readouterr().err
