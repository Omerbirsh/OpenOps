# v0 Read-Only Kubernetes Boundary

Safety is enforced outside the decision model by fixed intake validation, a dedicated Kubernetes identity, Kubernetes RBAC, and collectors that expose only predefined reads. Model instructions are not a security control.

## Two identities with separate purposes

Scenario setup and OpenOps runtime execution use different Kubernetes identities:

- `kind-openops-lab` is the administrative context created by `kind`. It may be used only by human-invoked scenario setup, fault, reset, verification, and teardown commands.
- `openops-reader@kind-openops-lab` is the only context accepted by the OpenOps CLI. It authenticates as ServiceAccount `openops-reader` in namespace `openops-lab`.

The runtime must load the explicitly named reader context. It must not use the current context, fall back to the administrative context, inherit a user's broader identity, or accept an arbitrary kubeconfig context.

## RBAC allowlist

The namespace Role for `openops-reader` permits only:

| API group | Resource | Verbs | Scope |
| --- | --- | --- | --- |
| `apps` | `deployments` | `get` | Deployment `readiness-demo` |
| core | `pods` | `get`, `list` | Namespace `openops-lab` |
| core | `events` | `get`, `list` | Namespace `openops-lab` |

No `watch` permission is required. The Role grants no access to ReplicaSets, Secrets, ConfigMaps, logs, nodes, or resources in another namespace.

RBAC cannot restrict a Pod or Event list by workload ownership. The Pod collector therefore uses the fixed label selector and discards nonmatching results. The Event collector queries and filters by the exact collected Deployment and Pod UIDs. This adapter filtering is required in addition to RBAC.

## Fixed execution allowlist

The runtime may execute only the three operations documented in the [architecture overview](../overview.md#fixed-collectors), in that order and at most once each.

Collector parameters come from the validated objective and fixed scenario constants. The model supplies none of them. There is no generic Kubernetes request function exposed to the model or CLI.

Before constructing a Kubernetes request, the runtime verifies:

- context is `openops-reader@kind-openops-lab`;
- namespace is `openops-lab`;
- workload kind is `Deployment`;
- workload name is `readiness-demo`; and
- the requested operation matches the current fixed collector.

Any mismatch fails before contacting Kubernetes.

## Forbidden capabilities

The runtime contains no path for:

- `create`, `update`, `patch`, `delete`, or `deletecollection`;
- Pod `exec`, `attach`, logs, port-forwarding, or ephemeral containers;
- node or host access;
- raw API paths or user-provided Kubernetes verbs;
- arbitrary `kubectl`, shell commands, command-line flags, or subprocesses;
- model-selected tools or model-authored parameters;
- modifying probes, restarting Pods, scaling workloads, or applying manifests.

The model may recommend a correction, but the report renderer is the end of the runtime path.

## Credential boundary

Kubernetes and model-provider credentials remain in their respective client/configuration layers. They are never fields in the objective, state, tool result, evidence, model context, report, or safe error summary.

The Kubernetes adapter must not serialize:

- kubeconfig content;
- bearer tokens or client certificates;
- authentication headers;
- complete client configuration;
- raw exception representations that may embed request details.

The model receives normalized evidence only.

## Raw and model-visible data

Allowlisted Kubernetes output is bounded and retained in-memory inside `ToolResult.data`. It is not automatically safe for the model. Only deterministic `EvidenceRecord` observations marked `internal` may enter model context.

Complete Event messages, annotations, labels other than the fixed selector, environment variables, volume definitions, and managed fields are excluded from model context. Raw output is not printed in the report or written to a persistent artifact by v0.

## Authorization failure

An authorization denial produces a failed `ToolResult` with:

- `error_category: authorization`;
- `retryable: false`; and
- a bounded message that names only the denied collector operation.

The runtime does not broaden the request, switch identity, or escalate permissions. The remaining fixed collectors are still attempted once, and the normal failure rules apply.

## Required negative verification

Phase 2 must verify with the runtime identity that required reads succeed and that Deployment mutation, Pod deletion, Secret reads, and Pod exec are denied. Collector tests must also prove that an invalid target is rejected before an SDK call and that unrelated listed objects are discarded.
