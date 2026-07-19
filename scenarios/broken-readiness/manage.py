"""Lifecycle commands for the disposable broken-readiness kind scenario.

This is human-invoked lab tooling. It is intentionally outside the ``openops``
runtime, which contains no shell or Kubernetes mutation path.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

CLUSTER_NAME = "openops-lab"
ADMIN_CONTEXT = "kind-openops-lab"
READER_CONTEXT = "openops-reader@kind-openops-lab"
NAMESPACE = "openops-lab"
DEPLOYMENT = "readiness-demo"
SELECTOR = "app.kubernetes.io/name=readiness-demo"
NODE_IMAGE = (
    "kindest/node:v1.36.1@sha256:3489c7674813ba5d8b1a9977baea8a6e553784dab7b84759d1014dbd78f7ebd5"
)

SCENARIO_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCENARIO_DIR.parents[1]
LAB_DIR = REPOSITORY_ROOT / ".openops-lab"
ADMIN_KUBECONFIG = LAB_DIR / "admin-kubeconfig"
READER_KUBECONFIG = LAB_DIR / "kubeconfig"


class ScenarioError(RuntimeError):
    """A bounded scenario lifecycle failure."""


def _require_tools() -> None:
    missing = [name for name in ("docker", "kind", "kubectl") if shutil.which(name) is None]
    if missing:
        raise ScenarioError(f"Missing required command(s): {', '.join(missing)}")


def _run(
    args: Sequence[str],
    *,
    capture: bool = False,
    timeout: int = 180,
) -> str:
    try:
        completed = subprocess.run(
            list(args),
            check=True,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as error:
        safe_detail = (error.stderr or error.stdout or "command failed").strip().splitlines()
        detail = safe_detail[-1] if safe_detail else "command failed"
        raise ScenarioError(f"{args[0]} failed: {detail[:300]}") from None
    except subprocess.TimeoutExpired:
        raise ScenarioError(f"{args[0]} timed out after {timeout} seconds") from None
    return completed.stdout if capture else ""


def _kubectl_admin(*args: str, capture: bool = False, timeout: int = 180) -> str:
    return _run(
        (
            "kubectl",
            "--kubeconfig",
            str(ADMIN_KUBECONFIG),
            "--context",
            ADMIN_CONTEXT,
            *args,
        ),
        capture=capture,
        timeout=timeout,
    )


def _kubectl_reader(*args: str, capture: bool = False, timeout: int = 180) -> str:
    return _run(
        (
            "kubectl",
            "--kubeconfig",
            str(READER_KUBECONFIG),
            "--context",
            READER_CONTEXT,
            *args,
        ),
        capture=capture,
        timeout=timeout,
    )


def _json(output: str) -> dict[str, Any]:
    value = json.loads(output)
    if not isinstance(value, dict):
        raise ScenarioError("kubectl returned an unexpected JSON document")
    return value


def _cluster_exists() -> bool:
    clusters = _run(("kind", "get", "clusters"), capture=True).splitlines()
    return CLUSTER_NAME in {item.strip() for item in clusters}


def create() -> None:
    """Create the pinned disposable kind cluster."""
    _require_tools()
    if _cluster_exists():
        raise ScenarioError(
            f"Cluster {CLUSTER_NAME!r} already exists; use 'teardown' before recreating it"
        )
    LAB_DIR.mkdir(parents=True, exist_ok=True)
    _run(
        (
            "kind",
            "create",
            "cluster",
            "--name",
            CLUSTER_NAME,
            "--image",
            NODE_IMAGE,
            "--config",
            str(SCENARIO_DIR / "kind.yaml"),
            "--kubeconfig",
            str(ADMIN_KUBECONFIG),
            "--wait",
            "120s",
        ),
        timeout=300,
    )
    print(f"Created disposable cluster {CLUSTER_NAME} with pinned node image.")


def _write_reader_kubeconfig() -> None:
    token = _kubectl_admin(
        "--namespace",
        NAMESPACE,
        "create",
        "token",
        "openops-reader",
        "--duration=8h",
        capture=True,
    ).strip()
    if not token:
        raise ScenarioError("Kubernetes returned an empty reader token")

    admin_config = _json(
        _run(
            (
                "kubectl",
                "--kubeconfig",
                str(ADMIN_KUBECONFIG),
                "config",
                "view",
                "--raw",
                "-o",
                "json",
            ),
            capture=True,
        )
    )
    clusters = admin_config.get("clusters", [])
    cluster = next(
        (
            item.get("cluster")
            for item in clusters
            if item.get("name") == ADMIN_CONTEXT and isinstance(item.get("cluster"), dict)
        ),
        None,
    )
    if not isinstance(cluster, dict):
        raise ScenarioError("Administrative kubeconfig does not contain the expected cluster")

    reader_config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [{"name": ADMIN_CONTEXT, "cluster": cluster}],
        "users": [{"name": "openops-reader", "user": {"token": token}}],
        "contexts": [
            {
                "name": READER_CONTEXT,
                "context": {
                    "cluster": ADMIN_CONTEXT,
                    "namespace": NAMESPACE,
                    "user": "openops-reader",
                },
            }
        ],
        "current-context": READER_CONTEXT,
    }
    READER_KUBECONFIG.write_text(json.dumps(reader_config, indent=2) + "\n", encoding="utf-8")
    with contextlib.suppress(OSError):
        READER_KUBECONFIG.chmod(stat.S_IRUSR | stat.S_IWUSR)


def setup() -> None:
    """Install the namespace, reader identity, and healthy workload."""
    _require_tools()
    if not _cluster_exists() or not ADMIN_KUBECONFIG.exists():
        raise ScenarioError("The lab cluster is absent; run 'create' first")
    for manifest in ("namespace.yaml", "rbac.yaml", "workload-healthy.yaml"):
        _kubectl_admin("apply", "-f", str(SCENARIO_DIR / manifest))
    _kubectl_admin(
        "--namespace",
        NAMESPACE,
        "rollout",
        "status",
        f"deployment/{DEPLOYMENT}",
        "--timeout=120s",
    )
    _write_reader_kubeconfig()
    verify_healthy()
    verify_rbac()
    print("Installed and verified the healthy baseline and read-only identity.")


def _workload_snapshot() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    deployment = _json(
        _kubectl_admin(
            "--namespace",
            NAMESPACE,
            "get",
            "deployment",
            DEPLOYMENT,
            "-o",
            "json",
            capture=True,
        )
    )
    pod_list = _json(
        _kubectl_admin(
            "--namespace",
            NAMESPACE,
            "get",
            "pods",
            "--selector",
            SELECTOR,
            "-o",
            "json",
            capture=True,
        )
    )
    pods = [item for item in pod_list.get("items", []) if isinstance(item, dict)]
    if len(pods) != 1:
        raise ScenarioError(f"Expected exactly one target Pod, observed {len(pods)}")
    pod_name = pods[0].get("metadata", {}).get("name", "")
    event_list = _json(
        _kubectl_admin(
            "--namespace",
            NAMESPACE,
            "get",
            "events",
            "--field-selector",
            f"involvedObject.kind=Pod,involvedObject.name={pod_name}",
            "-o",
            "json",
            capture=True,
        )
    )
    events = [item for item in event_list.get("items", []) if isinstance(item, dict)]
    return deployment, pods, events


def _probe_path(deployment: dict[str, Any]) -> str:
    containers = deployment["spec"]["template"]["spec"]["containers"]
    container = next(item for item in containers if item.get("name") == "web")
    return str(container["readinessProbe"]["httpGet"]["path"])


def verify_healthy() -> None:
    """Verify the exact healthy baseline."""
    deployment, pods, _ = _workload_snapshot()
    pod = pods[0]
    statuses = pod.get("status", {}).get("containerStatuses", [])
    web = next((item for item in statuses if item.get("name") == "web"), None)
    ready_condition = next(
        (
            item
            for item in pod.get("status", {}).get("conditions", [])
            if item.get("type") == "Ready"
        ),
        None,
    )
    checks = {
        "probe path is /": _probe_path(deployment) == "/",
        "one available replica": deployment.get("status", {}).get("availableReplicas", 0) == 1,
        "Pod phase is Running": pod.get("status", {}).get("phase") == "Running",
        "Pod Ready is True": ready_condition is not None
        and ready_condition.get("status") == "True",
        "container web is ready": web is not None and web.get("ready") is True,
        "container restart count is zero": web is not None and web.get("restartCount") == 0,
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise ScenarioError(f"Healthy baseline verification failed: {', '.join(failures)}")
    print("Healthy baseline verified.")


def _wait_for(check: Callable[[], None], description: str, timeout: int = 120) -> None:
    deadline = time.monotonic() + timeout
    last_error = "not ready"
    while time.monotonic() < deadline:
        try:
            check()
            return
        except ScenarioError as error:
            last_error = str(error)
            time.sleep(2)
    raise ScenarioError(f"Timed out waiting for {description}: {last_error}")


def fault() -> None:
    """Inject only the incorrect readiness path and verify the root cause."""
    _kubectl_admin("apply", "-f", str(SCENARIO_DIR / "workload-fault.yaml"))
    _wait_for(verify_fault, "the verified broken-readiness state")
    print("Injected and verified the single /ready readiness-probe fault.")


def verify_fault() -> None:
    """Verify the exact faulty state and its Kubernetes-reported root cause."""
    deployment, pods, events = _workload_snapshot()
    pod = pods[0]
    statuses = pod.get("status", {}).get("containerStatuses", [])
    web = next((item for item in statuses if item.get("name") == "web"), None)
    ready_condition = next(
        (
            item
            for item in pod.get("status", {}).get("conditions", [])
            if item.get("type") == "Ready"
        ),
        None,
    )
    has_probe_404 = any(
        event.get("reason") == "Unhealthy"
        and "readiness" in str(event.get("message", "")).lower()
        and "404" in str(event.get("message", ""))
        for event in events
    )
    checks = {
        "probe path is /ready": _probe_path(deployment) == "/ready",
        "zero available replicas": deployment.get("status", {}).get("availableReplicas", 0) == 0,
        "Pod phase is Running": pod.get("status", {}).get("phase") == "Running",
        "Pod Ready is False": ready_condition is not None
        and ready_condition.get("status") == "False",
        "container web is not ready": web is not None and web.get("ready") is False,
        "container restart count is zero": web is not None and web.get("restartCount") == 0,
        "readiness HTTP 404 Event exists": has_probe_404,
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise ScenarioError(f"Fault verification failed: {', '.join(failures)}")
    print("Fault verified: /ready returns HTTP 404 while the container remains running.")


def reset() -> None:
    """Restore and verify the healthy readiness path."""
    _kubectl_admin("apply", "-f", str(SCENARIO_DIR / "workload-healthy.yaml"))
    _kubectl_admin(
        "--namespace",
        NAMESPACE,
        "rollout",
        "status",
        f"deployment/{DEPLOYMENT}",
        "--timeout=120s",
    )
    verify_healthy()
    print("Reset and verified the healthy baseline.")


def _can_i(*args: str) -> bool:
    command = (
        "kubectl",
        "--kubeconfig",
        str(READER_KUBECONFIG),
        "--context",
        READER_CONTEXT,
        "auth",
        "can-i",
        *args,
    )
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise ScenarioError("kubectl auth can-i timed out") from None
    answer = completed.stdout.strip().lower()
    if completed.returncode in {0, 1} and answer in {"yes", "no"}:
        return answer == "yes"
    raise ScenarioError("kubectl auth can-i returned an unexpected result")


def verify_rbac() -> None:
    """Verify required reads and representative forbidden operations."""
    if not READER_KUBECONFIG.exists():
        raise ScenarioError("Reader kubeconfig is absent; run 'setup' first")
    allowed = {
        "get deployment/readiness-demo": _can_i(
            "get", f"deployment/{DEPLOYMENT}", "--namespace", NAMESPACE
        ),
        "list pods": _can_i("list", "pods", "--namespace", NAMESPACE),
        "list events": _can_i("list", "events", "--namespace", NAMESPACE),
    }
    denied = {
        "patch deployment/readiness-demo": _can_i(
            "patch", f"deployment/{DEPLOYMENT}", "--namespace", NAMESPACE
        ),
        "delete pods": _can_i("delete", "pods", "--namespace", NAMESPACE),
        "get secrets": _can_i("get", "secrets", "--namespace", NAMESPACE),
        "create pods/exec": _can_i("create", "pods/exec", "--namespace", NAMESPACE),
    }
    failed = [name for name, value in allowed.items() if not value]
    failed.extend(name for name, value in denied.items() if value)
    if failed:
        raise ScenarioError(f"Reader RBAC verification failed: {', '.join(failed)}")
    _kubectl_reader("--namespace", NAMESPACE, "get", "deployment", DEPLOYMENT, "-o", "name")
    print("Reader RBAC verified: required reads succeed and write/exec/secret access is denied.")


def teardown() -> None:
    """Delete only the explicitly named disposable cluster and local lab credentials."""
    _require_tools()
    if _cluster_exists():
        _run(("kind", "delete", "cluster", "--name", CLUSTER_NAME), timeout=180)
    if LAB_DIR.exists():
        shutil.rmtree(LAB_DIR)
    print(f"Removed disposable cluster {CLUSTER_NAME} and local lab credentials.")


COMMANDS: dict[str, Callable[[], None]] = {
    "create": create,
    "setup": setup,
    "verify-healthy": verify_healthy,
    "fault": fault,
    "verify-fault": verify_fault,
    "verify-rbac": verify_rbac,
    "reset": reset,
    "teardown": teardown,
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    arguments = parser.parse_args(argv)
    try:
        COMMANDS[arguments.command]()
    except ScenarioError as error:
        print(f"Scenario error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
