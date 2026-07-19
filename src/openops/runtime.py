"""One fixed collect-normalize-decide-validate-render workflow."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from openops.decision import (
    DecisionProvider,
    DiagnosisValidationError,
    ModelProviderError,
    validate_diagnosis,
)
from openops.models import (
    ErrorCategory,
    FailureStage,
    FailureSummary,
    InvestigationObjective,
    InvestigationOutcome,
    InvestigationPhase,
    InvestigationState,
    InvestigationStatus,
    SourceTool,
    ToolResult,
    ToolStatus,
)
from openops.normalizer import NormalizationError, normalize_evidence
from openops.report import render_report


class CollectorSuite(Protocol):
    def collect_deployment(
        self, objective: InvestigationObjective, tool_id: str = "tool-001"
    ) -> ToolResult: ...

    def collect_pods(
        self, objective: InvestigationObjective, tool_id: str = "tool-002"
    ) -> ToolResult: ...

    def collect_events(
        self,
        objective: InvestigationObjective,
        deployment_result: ToolResult,
        pod_result: ToolResult,
        tool_id: str = "tool-003",
    ) -> ToolResult: ...


def _unexpected_failure(tool_id: str, source: SourceTool) -> ToolResult:
    return ToolResult(
        id=tool_id,
        source_tool=source,
        collected_at=datetime.now(UTC),
        status=ToolStatus.FAILURE,
        data=None,
        raw_reference=None,
        error_category=ErrorCategory.EXECUTION_ERROR,
        error_message=f"{source.value} failed (execution_error).",
        retryable=False,
        duration_ms=0,
        truncated=False,
    )


def _finish_failed(
    state: InvestigationState,
    stage: FailureStage,
    category: ErrorCategory,
    message: str,
) -> InvestigationOutcome:
    state.phase = InvestigationPhase.FINISHED
    state.status = InvestigationStatus.FAILED
    state.failure = FailureSummary(stage=stage, category=category, message=message)
    return InvestigationOutcome(state=state, report=None)


def run_investigation(
    objective: InvestigationObjective,
    collectors: CollectorSuite,
    provider: DecisionProvider,
) -> InvestigationOutcome:
    state = InvestigationState(objective=objective)
    try:
        deployment = collectors.collect_deployment(objective, "tool-001")
    except Exception:
        deployment = _unexpected_failure("tool-001", SourceTool.DEPLOYMENT)
    state.tool_results.append(deployment)

    try:
        pods = collectors.collect_pods(objective, "tool-002")
    except Exception:
        pods = _unexpected_failure("tool-002", SourceTool.PODS)
    state.tool_results.append(pods)

    try:
        events = collectors.collect_events(objective, deployment, pods, "tool-003")
    except Exception:
        events = _unexpected_failure("tool-003", SourceTool.EVENTS)
    state.tool_results.append(events)

    try:
        state.evidence.extend(
            normalize_evidence(
                objective,
                state.tool_results,
                limit=state.limits.max_evidence_records,
            )
        )
    except NormalizationError:
        return _finish_failed(
            state,
            FailureStage.NORMALIZATION,
            ErrorCategory.MALFORMED_RESPONSE,
            "Deterministic evidence normalization failed.",
        )
    if not state.evidence:
        return _finish_failed(
            state,
            FailureStage.COLLECTION,
            ErrorCategory.MALFORMED_RESPONSE,
            "Collection produced no usable evidence.",
        )

    state.phase = InvestigationPhase.DECIDING
    try:
        candidate = provider.diagnose(objective, tuple(state.evidence))
    except ModelProviderError:
        return _finish_failed(
            state,
            FailureStage.MODEL,
            ErrorCategory.UNAVAILABLE,
            "The decision model call failed.",
        )
    except Exception:
        return _finish_failed(
            state,
            FailureStage.MODEL,
            ErrorCategory.EXECUTION_ERROR,
            "The decision model call failed.",
        )

    try:
        decision = validate_diagnosis(candidate, state.evidence)
    except DiagnosisValidationError:
        return _finish_failed(
            state,
            FailureStage.VALIDATION,
            ErrorCategory.MALFORMED_RESPONSE,
            "The candidate diagnosis failed independent validation.",
        )

    state.decision = decision
    state.phase = InvestigationPhase.FINISHED
    state.status = InvestigationStatus.COMPLETED
    return InvestigationOutcome(state=state, report=render_report(state))
