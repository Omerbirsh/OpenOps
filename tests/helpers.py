"""Deterministic fixtures shared by unit tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from openops.models import (
    ErrorCategory,
    InvestigationObjective,
    SourceTool,
    ToolResult,
    ToolStatus,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "broken_readiness"


def objective() -> InvestigationObjective:
    return InvestigationObjective(
        cluster_context="openops-reader@kind-openops-lab",
        namespace="openops-lab",
        workload_kind="Deployment",
        workload_name="readiness-demo",
        symptom="Pod is Running but not Ready",
        time_window_seconds=1800,
    )


def fixture_result(name: str) -> ToolResult:
    return ToolResult.model_validate_json(
        (FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8")
    )


class FixtureCollectors:
    def __init__(self, *, fail_deployment: bool = False) -> None:
        self.calls: list[str] = []
        self.fail_deployment = fail_deployment

    def collect_deployment(
        self, objective: InvestigationObjective, tool_id: str = "tool-001"
    ) -> ToolResult:
        del objective, tool_id
        self.calls.append("deployment")
        if self.fail_deployment:
            raise RuntimeError("untrusted SDK failure")
        return fixture_result("deployment")

    def collect_pods(
        self, objective: InvestigationObjective, tool_id: str = "tool-002"
    ) -> ToolResult:
        del objective, tool_id
        self.calls.append("pods")
        return fixture_result("pods")

    def collect_events(
        self,
        objective: InvestigationObjective,
        deployment_result: ToolResult,
        pod_result: ToolResult,
        tool_id: str = "tool-003",
    ) -> ToolResult:
        del objective, deployment_result, pod_result, tool_id
        self.calls.append("events")
        return fixture_result("events")


def failed_result(tool_id: str, source: SourceTool) -> ToolResult:
    return ToolResult(
        id=tool_id,
        source_tool=source,
        collected_at=datetime(2026, 7, 19, 12, 0, tzinfo=UTC),
        status=ToolStatus.FAILURE,
        data=None,
        raw_reference=None,
        error_category=ErrorCategory.UNAVAILABLE,
        error_message=f"{source.value} failed (unavailable).",
        retryable=True,
        duration_ms=1,
        truncated=False,
    )


class NoEvidenceCollectors:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def collect_deployment(
        self, objective: InvestigationObjective, tool_id: str = "tool-001"
    ) -> ToolResult:
        del objective
        self.calls.append("deployment")
        return failed_result(tool_id, SourceTool.DEPLOYMENT)

    def collect_pods(
        self, objective: InvestigationObjective, tool_id: str = "tool-002"
    ) -> ToolResult:
        del objective
        self.calls.append("pods")
        return failed_result(tool_id, SourceTool.PODS)

    def collect_events(
        self,
        objective: InvestigationObjective,
        deployment_result: ToolResult,
        pod_result: ToolResult,
        tool_id: str = "tool-003",
    ) -> ToolResult:
        del objective, deployment_result, pod_result
        self.calls.append("events")
        return failed_result(tool_id, SourceTool.EVENTS)
