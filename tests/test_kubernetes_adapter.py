"""Unit tests for allowlisted Kubernetes SDK serialization."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from kubernetes.client.exceptions import ApiException

from openops.kubernetes_adapter import KubernetesCollectorSuite
from openops.models import DeploymentData, EventsData, PodsData
from tests.helpers import objective

pytestmark = pytest.mark.unit


def _ns(**values: Any) -> SimpleNamespace:
    return SimpleNamespace(**values)


def _deployment() -> SimpleNamespace:
    probe = _ns(
        http_get=_ns(scheme="HTTP", path="/ready", port=80),
        initial_delay_seconds=0,
        period_seconds=2,
        timeout_seconds=1,
        success_threshold=1,
        failure_threshold=1,
    )
    return _ns(
        metadata=_ns(
            uid="deployment-uid", name="readiness-demo", namespace="openops-lab", generation=2
        ),
        spec=_ns(
            replicas=1,
            strategy=_ns(type="Recreate"),
            selector=_ns(match_labels={"app.kubernetes.io/name": "readiness-demo"}),
            template=_ns(spec=_ns(containers=[_ns(name="web", readiness_probe=probe)])),
        ),
        status=_ns(
            ready_replicas=0,
            available_replicas=0,
            unavailable_replicas=1,
            observed_generation=2,
            conditions=[_ns(type="Available", status="False", reason="Unavailable")],
        ),
    )


def _pod(*, name: str, label: str = "readiness-demo") -> SimpleNamespace:
    return _ns(
        metadata=_ns(
            uid=f"{name}-uid",
            name=name,
            namespace="openops-lab",
            labels={"app.kubernetes.io/name": label},
            owner_references=[_ns(uid="replicaset-uid")],
        ),
        status=_ns(
            phase="Running",
            conditions=[_ns(type="Ready", status="False", reason="ContainersNotReady")],
            container_statuses=[
                _ns(
                    name="web",
                    ready=False,
                    restart_count=0,
                    state=_ns(waiting=None, running=_ns(), terminated=None),
                )
            ],
        ),
    )


class _Apps:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def read_namespaced_deployment(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return _deployment()


class _Core:
    def __init__(self) -> None:
        self.pod_calls: list[dict[str, Any]] = []
        self.event_calls: list[dict[str, Any]] = []

    def list_namespaced_pod(self, **kwargs: Any) -> SimpleNamespace:
        self.pod_calls.append(kwargs)
        return _ns(items=[_pod(name="readiness-demo-z"), _pod(name="unrelated", label="other")])

    def list_namespaced_event(self, **kwargs: Any) -> SimpleNamespace:
        self.event_calls.append(kwargs)
        event = _ns(
            metadata=_ns(uid="event-uid"),
            involved_object=_ns(
                uid="readiness-demo-z-uid",
                kind="Pod",
                namespace="openops-lab",
                name="readiness-demo-z",
            ),
            type="Warning",
            reason="Unhealthy",
            message="Readiness probe failed: HTTP probe failed with statuscode: 404",
            count=2,
            series=None,
            first_timestamp=datetime(2026, 7, 19, 11, 59, tzinfo=UTC),
            last_timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=UTC),
            event_time=None,
        )
        unrelated = _ns(
            metadata=_ns(uid="unrelated-event"),
            involved_object=_ns(uid="other-uid", kind="Pod", namespace="openops-lab", name="other"),
            type="Warning",
            reason="Unhealthy",
            message="Readiness probe failed: HTTP probe failed with statuscode: 500",
            count=1,
            series=None,
            first_timestamp=datetime(2026, 7, 19, 11, 59, tzinfo=UTC),
            last_timestamp=datetime(2026, 7, 19, 12, 0, tzinfo=UTC),
            event_time=None,
        )
        return _ns(items=[event, unrelated])


def _suite(apps: _Apps | None = None, core: _Core | None = None) -> KubernetesCollectorSuite:
    return KubernetesCollectorSuite(
        apps or _Apps(),
        core or _Core(),
        now=lambda: datetime(2026, 7, 19, 12, 1, tzinfo=UTC),
        monotonic=lambda: 1.0,
    )


def test_collectors_allowlist_and_locally_filter_sdk_objects() -> None:
    core = _Core()
    suite = _suite(core=core)
    deployment = suite.collect_deployment(objective())
    pods = suite.collect_pods(objective())
    events = suite.collect_events(objective(), deployment, pods)

    assert isinstance(deployment.data, DeploymentData)
    assert deployment.data.containers[0].readiness_probe is not None
    assert deployment.data.containers[0].readiness_probe.path == "/ready"
    assert isinstance(pods.data, PodsData)
    assert [item.name for item in pods.data.pods] == ["readiness-demo-z"]
    assert isinstance(events.data, EventsData)
    assert [item.uid for item in events.data.events] == ["event-uid"]
    assert core.pod_calls[0]["label_selector"] == "app.kubernetes.io/name=readiness-demo"
    assert {call["field_selector"] for call in core.event_calls} == {
        "involvedObject.uid=deployment-uid",
        "involvedObject.uid=readiness-demo-z-uid",
    }


def test_authorization_error_is_bounded_without_raw_exception() -> None:
    apps = _Apps(error=ApiException(status=403, reason="token=do-not-copy"))
    result = _suite(apps=apps).collect_deployment(objective())
    assert result.status.value == "failure"
    assert result.error_category is not None
    assert result.error_category.value == "authorization"
    assert result.error_message == "Deployment read failed (authorization)."
    assert "token" not in result.error_message
