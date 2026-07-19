"""Sanitized trace rendering with no raw collector data or credentials."""

from __future__ import annotations

import json
from pathlib import Path

from openops.models import InvestigationState
from openops.report import collection_warnings


def sanitized_trace(state: InvestigationState) -> dict[str, object]:
    return {
        "objective": state.objective.model_dump(mode="json"),
        "phase": state.phase.value,
        "status": state.status.value,
        "collector_summaries": [
            {
                "id": result.id,
                "source_tool": result.source_tool.value,
                "status": result.status.value,
                "error_category": (
                    result.error_category.value if result.error_category is not None else None
                ),
                "duration_ms": result.duration_ms,
                "truncated": result.truncated,
            }
            for result in state.tool_results
        ],
        "evidence": [
            {
                "id": item.id,
                "source_tool": item.source_tool.value,
                "timestamp": item.timestamp.isoformat(),
                "target": item.target.model_dump(mode="json"),
                "observation": item.observation,
            }
            for item in state.evidence
        ],
        "decision": state.decision.model_dump(mode="json") if state.decision else None,
        "failure": state.failure.model_dump(mode="json") if state.failure else None,
        "collection_warnings": collection_warnings(state),
    }


def write_sanitized_trace(state: InvestigationState, path: Path) -> None:
    """Create a new trace without overwriting an existing artifact."""
    payload = json.dumps(sanitized_trace(state), indent=2, sort_keys=True) + "\n"
    with path.open("x", encoding="utf-8") as output:
        output.write(payload)
