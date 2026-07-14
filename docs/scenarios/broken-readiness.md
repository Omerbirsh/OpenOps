# Reference Scenario: Broken HTTP Readiness Path

This is the only v0 implementation, demo, and live-evaluation scenario. Phase 2 manifests and lifecycle commands must implement this specification exactly.

## Fixed identities

| Item | Value |
| --- | --- |
| `kind` cluster name | `openops-lab` |
| Administrative context | `kind-openops-lab` |
| Runtime read-only context | `openops-reader@kind-openops-lab` |
| Namespace | `openops-lab` |
| ServiceAccount | `openops-reader` |
| Deployment | `readiness-demo` |
| Replica count | 1 |
| Container | `web` |
| Selector label | `app.kubernetes.io/name=readiness-demo` |
| Container port | 80 |

The workload uses the official image `nginx:1.27.5-alpine@sha256:65645c7bb6a0661892a8b03b89d0743208a18dd2f3f17a54ef4b76fb8e2f2a10`. The tag documents the intended release and the multi-platform manifest digest makes the scenario input immutable.

The Deployment strategy is `Recreate`. This is required so fault injection removes the healthy Pod before creating the faulty Pod; a default rolling update could leave the old ready Pod available and make the expected Deployment status ambiguous.

## Application behavior

The NGINX process listens on container port 80.

- `GET /` returns HTTP 200 and is the valid endpoint used by the healthy baseline.
- `GET /ready` returns HTTP 404 because no such resource exists.
- The process remains running when either endpoint is probed.

No Service or external network dependency is required. The kubelet performs the probe directly against the Pod.

## Healthy baseline

Before fault injection, the Deployment uses this readiness probe:

| Setting | Value |
| --- | --- |
| Type | HTTP GET |
| Scheme | HTTP |
| Path | `/` |
| Port | 80 |
| `initialDelaySeconds` | 0 |
| `periodSeconds` | 2 |
| `timeoutSeconds` | 1 |
| `successThreshold` | 1 |
| `failureThreshold` | 1 |

The baseline is valid only when:

- the Deployment has one available replica;
- the Pod phase is `Running`;
- the Pod Ready condition is `True`;
- container `web` is ready; and
- its restart count is zero.

The setup workflow must verify this state before applying the fault.

## Single injected fault

Fault injection changes exactly one field:

```text
readinessProbe.httpGet.path: / -> /ready
```

Every other image, port, probe setting, replica setting, label, and application behavior remains unchanged.

## Expected faulty state

After the `Recreate` rollout replaces the healthy Pod and at least two probe periods have elapsed:

- exactly one target Pod exists;
- the Pod phase is `Running`;
- the Pod Ready condition is `False`;
- container `web` has `ready: false`;
- its restart count is zero;
- the Deployment has one desired replica and zero available replicas;
- the stored Deployment probe configuration shows HTTP path `/ready` on port 80; and
- a target Pod Event has type `Warning`, reason `Unhealthy`, and reports a readiness-probe HTTP 404 failure.

Kubernetes versions may vary the complete Event sentence. Evaluation matches the involved Pod, `Unhealthy` reason, readiness-probe meaning, and HTTP status 404 rather than one exact message string.

## Ground truth

The application process is healthy and responding over HTTP. Kubernetes cannot mark the Pod Ready because the configured readiness path `/ready` returns 404. The valid baseline endpoint is `/`.

The expected cause is:

> The Pod remains unready because its HTTP readiness probe requests `/ready` on port 80 and receives HTTP 404.

Expected confidence is `high` when the report cites all three evidence categories:

1. the configured readiness path and port;
2. the running-but-unready Pod/container state with zero restarts; and
3. the `Unhealthy` readiness-probe Event with HTTP 404.

The expected recommendation is to configure the readiness probe to use an endpoint that returns a successful status, `/` in this reference application. OpenOps does not apply the change.

## Required absence of distractions

The scenario is invalid if any of the following occurs:

- image pull failure;
- scheduling failure;
- CrashLoopBackOff or application exit;
- container restart;
- incorrect container port;
- DNS or external networking dependency;
- resource pressure or node failure;
- liveness or startup probe failure;
- second workload failure; or
- missing read-only authorization.

## Lifecycle requirements for Phase 2

The implementation must provide one documented entry point for each action:

1. create the pinned `kind` cluster;
2. install the namespace, read-only identity, and healthy workload;
3. verify the healthy baseline;
4. inject only the readiness-path fault;
5. verify the expected faulty state;
6. reset to and verify the healthy baseline; and
7. tear down the cluster.

These lifecycle actions run under the administrative context and are scenario tooling, not OpenOps runtime capabilities.

## Forbidden OpenOps actions

During investigation OpenOps must not modify the Deployment, change the probe, restart or delete the Pod, read container logs, execute in the container, create a resource, switch to the administrative context, or perform remediation.
