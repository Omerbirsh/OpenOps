"""Deterministic conversion from bounded tool data to factual evidence."""

from __future__ import annotations

from collections.abc import Iterable

from openops.kubernetes_adapter import extract_http_status
from openops.models import (
    DeploymentData,
    EventsData,
    EvidenceRecord,
    EvidenceTarget,
    InvestigationObjective,
    PodData,
    PodsData,
    Sensitivity,
    ToolResult,
    ToolStatus,
)


class NormalizationError(ValueError):
    """The bounded results could not produce a valid evidence set."""


def _target(
    objective: InvestigationObjective, resource_kind: str, resource_name: str
) -> EvidenceTarget:
    return EvidenceTarget(
        cluster_context=objective.cluster_context,
        namespace=objective.namespace,
        resource_kind=resource_kind,
        resource_name=resource_name,
    )


def _pod_observations(pod: PodData) -> Iterable[str]:
    ready = next((item.status for item in pod.conditions if item.type == "Ready"), "Unknown")
    yield f"Pod {pod.name} is {pod.phase} and its Ready condition is {ready}."
    for container in pod.containers:
        readiness = "ready" if container.ready else "not ready"
        yield (
            f"Container {container.name} is {container.state}, is {readiness}, "
            f"and has restarted {container.restart_count} times."
        )


def normalize_evidence(
    objective: InvestigationObjective,
    results: list[ToolResult],
    *,
    limit: int = 20,
) -> list[EvidenceRecord]:
    pending: list[tuple[ToolResult, EvidenceTarget, str]] = []
    for result in results:
        if result.status is ToolStatus.FAILURE or result.data is None:
            continue
        if result.raw_reference is None:
            raise NormalizationError("usable collector data has no raw reference")
        data = result.data
        if isinstance(data, DeploymentData):
            deployment_target = _target(objective, "Deployment", data.name)
            pending.append(
                (
                    result,
                    deployment_target,
                    (
                        f"Deployment {data.name} has {data.desired_replicas} desired replica "
                        f"and {data.available_replicas} available replicas."
                    ),
                )
            )
            for container in data.containers:
                probe = container.readiness_probe
                if probe is None:
                    continue
                pending.append(
                    (
                        result,
                        deployment_target,
                        (
                            f"Container {container.name} has an HTTP readiness probe configured "
                            f"for path {probe.path} on port {probe.port}."
                        ),
                    )
                )
        elif isinstance(data, PodsData):
            for pod in data.pods:
                pod_target = _target(objective, "Pod", pod.name)
                pending.extend((result, pod_target, text) for text in _pod_observations(pod))
        elif isinstance(data, EventsData):
            for event in data.events:
                message = event.message
                status = extract_http_status(message)
                if (
                    event.reason != "Unhealthy"
                    or "readiness" not in message.lower()
                    or status is None
                ):
                    continue
                event_target = _target(
                    objective,
                    event.involved_object.kind,
                    event.involved_object.name,
                )
                pending.append(
                    (
                        result,
                        event_target,
                        (
                            "Kubernetes reported an Unhealthy readiness probe result with HTTP "
                            f"status {status} for {event.involved_object.kind} "
                            f"{event.involved_object.name}."
                        ),
                    )
                )

    if len(pending) > limit:
        raise NormalizationError(f"normalization exceeded the fixed {limit}-record limit")

    evidence: list[EvidenceRecord] = []
    for sequence, (result, target, observation) in enumerate(pending, start=1):
        evidence.append(
            EvidenceRecord(
                id=f"evidence-{sequence:03d}",
                source_tool=result.source_tool,
                timestamp=result.collected_at,
                target=target,
                observation=observation,
                sensitivity=Sensitivity.INTERNAL,
                raw_reference=result.raw_reference or "",
            )
        )
    return evidence
