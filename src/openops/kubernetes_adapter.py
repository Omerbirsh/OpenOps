"""Fixed, read-only Kubernetes collectors for the v0 scenario."""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from kubernetes.config.config_exception import ConfigException

from openops.models import (
    DeploymentContainer,
    DeploymentData,
    ErrorCategory,
    EventData,
    EventsData,
    InvestigationObjective,
    InvolvedObject,
    KubernetesCondition,
    PodContainer,
    PodData,
    PodsData,
    ReadinessProbe,
    SourceTool,
    ToolData,
    ToolResult,
    ToolStatus,
)

_SELECTOR_KEY = "app.kubernetes.io/name"
_SELECTOR_VALUE = "readiness-demo"
_SELECTOR = f"{_SELECTOR_KEY}={_SELECTOR_VALUE}"
_RESULT_LIMIT_BYTES = 65_536
_EVENT_LIMIT = 20
_REQUEST_TIMEOUT_SECONDS = 15


class KubernetesConfigurationError(RuntimeError):
    """Safe local configuration failure before collection begins."""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _condition(item: Any) -> KubernetesCondition:
    return KubernetesCondition(
        type=str(item.type or ""),
        status=str(item.status or ""),
        reason=str(item.reason) if item.reason else None,
    )


def _datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return None


def _pod_state(container_status: Any) -> str:
    state = container_status.state
    if state is None:
        return "unknown"
    if state.waiting is not None:
        return "waiting"
    if state.running is not None:
        return "running"
    if state.terminated is not None:
        return "terminated"
    return "unknown"


def _error_category(error: Exception) -> tuple[ErrorCategory, bool]:
    if isinstance(error, ApiException):
        status = error.status
        if status == 401:
            return ErrorCategory.AUTHENTICATION, False
        if status == 403:
            return ErrorCategory.AUTHORIZATION, False
        if status == 404:
            return ErrorCategory.NOT_FOUND, False
        if status in {408, 504}:
            return ErrorCategory.TIMEOUT, True
        if status == 429 or status >= 500:
            return ErrorCategory.UNAVAILABLE, True
    if isinstance(error, TimeoutError):
        return ErrorCategory.TIMEOUT, True
    return ErrorCategory.EXECUTION_ERROR, False


def _safe_error_message(source: SourceTool, category: ErrorCategory) -> str:
    operation = {
        SourceTool.DEPLOYMENT: "Deployment read",
        SourceTool.PODS: "Pod list",
        SourceTool.EVENTS: "Event list",
    }[source]
    return f"{operation} failed ({category.value})."


def _serialized_size(data: ToolData) -> int:
    payload = json.dumps(data.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return len(payload.encode("utf-8"))


def _trim_to_limit(data: ToolData) -> tuple[ToolData, bool]:
    if _serialized_size(data) <= _RESULT_LIMIT_BYTES:
        return data, False
    if isinstance(data, PodsData):
        items = list(data.pods)
        while items:
            items.pop()
            pod_candidate = PodsData(pods=tuple(items))
            if _serialized_size(pod_candidate) <= _RESULT_LIMIT_BYTES:
                return pod_candidate, True
    if isinstance(data, EventsData):
        events = list(data.events)
        while events:
            events.pop()
            event_candidate = EventsData(events=tuple(events))
            if _serialized_size(event_candidate) <= _RESULT_LIMIT_BYTES:
                return event_candidate, True
    raise ValueError("allowlisted collector output exceeds the fixed result limit")


class KubernetesCollectorSuite:
    """Three fixed collectors sharing one explicitly configured API client."""

    def __init__(
        self,
        apps_api: Any,
        core_api: Any,
        *,
        now: Callable[[], datetime] = _utcnow,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._apps_api = apps_api
        self._core_api = core_api
        self._now = now
        self._monotonic = monotonic

    def _execute(
        self,
        tool_id: str,
        source: SourceTool,
        operation: Callable[[], ToolData],
    ) -> ToolResult:
        started = self._monotonic()
        try:
            data, truncated = _trim_to_limit(operation())
        except Exception as error:  # Kubernetes SDK exposes several transport exception types.
            category, retryable = _error_category(error)
            duration = max(0, round((self._monotonic() - started) * 1000))
            return ToolResult(
                id=tool_id,
                source_tool=source,
                collected_at=self._now(),
                status=ToolStatus.FAILURE,
                data=None,
                raw_reference=None,
                error_category=category,
                error_message=_safe_error_message(source, category),
                retryable=retryable,
                duration_ms=duration,
                truncated=False,
            )
        duration = max(0, round((self._monotonic() - started) * 1000))
        return ToolResult(
            id=tool_id,
            source_tool=source,
            collected_at=self._now(),
            status=ToolStatus.SUCCESS,
            data=data,
            raw_reference=f"tool-result:{tool_id}#/data",
            error_category=None,
            error_message=None,
            retryable=False,
            duration_ms=duration,
            truncated=truncated,
        )

    def collect_deployment(
        self, objective: InvestigationObjective, tool_id: str = "tool-001"
    ) -> ToolResult:
        def operation() -> DeploymentData:
            deployment = self._apps_api.read_namespaced_deployment(
                name=objective.workload_name,
                namespace=objective.namespace,
                _request_timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            selector = dict(sorted((deployment.spec.selector.match_labels or {}).items()))
            containers: list[DeploymentContainer] = []
            for item in sorted(
                deployment.spec.template.spec.containers, key=lambda value: value.name
            ):
                probe = item.readiness_probe
                http_get = probe.http_get if probe is not None else None
                readiness_probe = None
                if probe is not None and http_get is not None:
                    readiness_probe = ReadinessProbe(
                        type="http_get",
                        scheme=str(http_get.scheme or "HTTP"),
                        path=str(http_get.path or ""),
                        port=http_get.port,
                        initial_delay_seconds=int(probe.initial_delay_seconds or 0),
                        period_seconds=int(probe.period_seconds or 10),
                        timeout_seconds=int(probe.timeout_seconds or 1),
                        success_threshold=int(probe.success_threshold or 1),
                        failure_threshold=int(probe.failure_threshold or 3),
                    )
                containers.append(
                    DeploymentContainer(name=str(item.name), readiness_probe=readiness_probe)
                )
            conditions = tuple(
                sorted(
                    (_condition(item) for item in (deployment.status.conditions or [])),
                    key=lambda item: (item.type, item.status, item.reason or ""),
                )
            )
            return DeploymentData(
                uid=str(deployment.metadata.uid),
                name=str(deployment.metadata.name),
                namespace=str(deployment.metadata.namespace),
                generation=int(deployment.metadata.generation or 0),
                desired_replicas=int(deployment.spec.replicas or 0),
                ready_replicas=int(deployment.status.ready_replicas or 0),
                available_replicas=int(deployment.status.available_replicas or 0),
                unavailable_replicas=int(deployment.status.unavailable_replicas or 0),
                observed_generation=deployment.status.observed_generation,
                strategy=str(deployment.spec.strategy.type or ""),
                selector=selector,
                containers=tuple(containers),
                conditions=conditions,
            )

        return self._execute(tool_id, SourceTool.DEPLOYMENT, operation)

    def collect_pods(
        self, objective: InvestigationObjective, tool_id: str = "tool-002"
    ) -> ToolResult:
        def operation() -> PodsData:
            response = self._core_api.list_namespaced_pod(
                namespace=objective.namespace,
                label_selector=_SELECTOR,
                limit=20,
                _request_timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            pods: list[PodData] = []
            for item in response.items or []:
                labels = item.metadata.labels or {}
                if labels.get(_SELECTOR_KEY) != _SELECTOR_VALUE:
                    continue
                conditions = tuple(
                    sorted(
                        (_condition(value) for value in (item.status.conditions or [])),
                        key=lambda value: (value.type, value.status, value.reason or ""),
                    )
                )
                containers = tuple(
                    PodContainer(
                        name=str(value.name),
                        ready=bool(value.ready),
                        restart_count=int(value.restart_count or 0),
                        state=cast(Any, _pod_state(value)),
                    )
                    for value in sorted(
                        item.status.container_statuses or [], key=lambda current: current.name
                    )
                )
                owner_uids = tuple(
                    sorted(
                        str(value.uid)
                        for value in (item.metadata.owner_references or [])
                        if value.uid
                    )
                )
                pods.append(
                    PodData(
                        uid=str(item.metadata.uid),
                        name=str(item.metadata.name),
                        namespace=str(item.metadata.namespace),
                        owner_uids=owner_uids,
                        phase=str(item.status.phase or "Unknown"),
                        conditions=conditions,
                        containers=containers,
                    )
                )
            return PodsData(pods=tuple(sorted(pods, key=lambda value: value.name)))

        return self._execute(tool_id, SourceTool.PODS, operation)

    def collect_events(
        self,
        objective: InvestigationObjective,
        deployment_result: ToolResult,
        pod_result: ToolResult,
        tool_id: str = "tool-003",
    ) -> ToolResult:
        def operation() -> EventsData:
            target_uids: set[str] = set()
            if isinstance(deployment_result.data, DeploymentData):
                target_uids.add(deployment_result.data.uid)
            if isinstance(pod_result.data, PodsData):
                target_uids.update(item.uid for item in pod_result.data.pods)
            if not target_uids:
                raise ValueError("event collection requires a collected target UID")

            cutoff = self._now() - timedelta(seconds=objective.time_window_seconds)
            by_uid: dict[str, EventData] = {}
            for target_uid in sorted(target_uids):
                response = self._core_api.list_namespaced_event(
                    namespace=objective.namespace,
                    field_selector=f"involvedObject.uid={target_uid}",
                    limit=100,
                    _request_timeout=_REQUEST_TIMEOUT_SECONDS,
                )
                for item in response.items or []:
                    involved = item.involved_object
                    if str(involved.uid or "") not in target_uids:
                        continue
                    last_seen = _datetime(
                        getattr(getattr(item, "series", None), "last_observed_time", None)
                    )
                    last_seen = last_seen or _datetime(item.last_timestamp)
                    last_seen = last_seen or _datetime(getattr(item, "event_time", None))
                    first_seen = _datetime(item.first_timestamp)
                    first_seen = first_seen or _datetime(getattr(item, "event_time", None))
                    if last_seen is not None and last_seen < cutoff:
                        continue
                    event_uid = str(item.metadata.uid or "")
                    if not event_uid:
                        continue
                    series_count = getattr(getattr(item, "series", None), "count", None)
                    by_uid[event_uid] = EventData(
                        uid=event_uid,
                        type=str(item.type or ""),
                        reason=str(item.reason or ""),
                        message=str(item.message or "")[:512],
                        count=int(item.count or series_count or 1),
                        first_seen=first_seen,
                        last_seen=last_seen,
                        involved_object=InvolvedObject(
                            uid=str(involved.uid or ""),
                            kind=str(involved.kind or ""),
                            namespace=str(involved.namespace or ""),
                            name=str(involved.name or ""),
                        ),
                    )

            def sort_key(event: EventData) -> tuple[int, float, str, str, str]:
                if event.last_seen is None:
                    time_key = (1, 0.0)
                else:
                    time_key = (0, -event.last_seen.timestamp())
                return (
                    time_key[0],
                    time_key[1],
                    event.involved_object.uid,
                    event.reason,
                    event.uid,
                )

            ordered = tuple(sorted(by_uid.values(), key=sort_key)[:_EVENT_LIMIT])
            return EventsData(events=ordered)

        return self._execute(tool_id, SourceTool.EVENTS, operation)


def build_live_collector_suite(objective: InvestigationObjective) -> KubernetesCollectorSuite:
    """Load only the explicitly validated reader context."""
    if objective.cluster_context != "openops-reader@kind-openops-lab":
        raise KubernetesConfigurationError("Refusing to load an unapproved Kubernetes context")
    kubeconfig = os.environ.get("OPENOPS_KUBECONFIG") or os.environ.get("KUBECONFIG")
    try:
        api_client = config.new_client_from_config(
            config_file=kubeconfig,
            context=objective.cluster_context,
            persist_config=False,
        )
    except (ConfigException, OSError):
        raise KubernetesConfigurationError(
            "Could not load the explicit openops-reader Kubernetes context."
        ) from None
    return KubernetesCollectorSuite(
        apps_api=client.AppsV1Api(api_client),
        core_api=client.CoreV1Api(api_client),
    )


def extract_http_status(message: str) -> int | None:
    """Extract only a recognized HTTP status from untrusted Event text."""
    match = re.search(r"(?:statuscode:\s*|status(?: code)?\s+)([1-5][0-9]{2})\b", message, re.I)
    return int(match.group(1)) if match else None
