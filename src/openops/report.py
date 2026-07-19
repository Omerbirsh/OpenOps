"""Human-readable rendering for validated completed investigations."""

from __future__ import annotations

from openops.models import InvestigationState, InvestigationStatus, ToolStatus


def collection_warnings(state: InvestigationState) -> list[str]:
    warnings: list[str] = []
    for result in state.tool_results:
        if result.status is not ToolStatus.SUCCESS:
            warnings.append(result.error_message or f"{result.source_tool.value} did not succeed.")
        if result.truncated:
            warnings.append(f"{result.source_tool.value} output was truncated to the fixed limit.")
    return warnings


def render_report(state: InvestigationState) -> str:
    if state.status is not InvestigationStatus.COMPLETED or state.decision is None:
        raise ValueError("only a completed validated investigation can be rendered")
    objective = state.objective
    evidence_by_id = {item.id: item for item in state.evidence}
    lines = [
        "OpenOps investigation report",
        "",
        "Target",
        f"  Context: {objective.cluster_context}",
        f"  Namespace: {objective.namespace}",
        f"  Workload: {objective.workload_kind}/{objective.workload_name}",
        "",
        "Reported symptom (user-provided context)",
        f"  {objective.symptom}",
        "",
        "Diagnosis",
        f"  Cause: {state.decision.cause}",
        f"  Confidence: {state.decision.confidence.value}",
        "",
        "Cited evidence",
    ]
    for evidence_id in state.decision.evidence_ids:
        item = evidence_by_id[evidence_id]
        target = f"{item.target.resource_kind}/{item.target.resource_name}"
        lines.extend(
            (
                f"  {item.id}: {item.observation}",
                f"    Source: {item.source_tool.value}; target: {target}",
            )
        )
    lines.extend(("", "Alternatives or uncertainty"))
    if state.decision.alternatives:
        lines.extend(f"  - {item}" for item in state.decision.alternatives)
    else:
        lines.append("  None stated")
    lines.extend(("", "Recommendation", f"  {state.decision.recommendation}"))
    lines.extend(("", "Collection warnings"))
    warnings = collection_warnings(state)
    lines.extend((f"  - {item}" for item in warnings) if warnings else ("  None",))
    return "\n".join(lines) + "\n"
