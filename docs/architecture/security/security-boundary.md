# Read-Only Kubernetes Authorization Boundary

OpenOps operates with a dedicated Kubernetes identity restricted to the minimum read permissions required by the first workflow.

Safety is enforced by Kubernetes authorization and the tool adapter. It does not depend on model instructions or model compliance.

---

## Permitted Operations

OpenOps may perform only read-equivalent Kubernetes operations.

Allowed verbs:

* `get`
* `list`
* `watch`

For the first workflow, the runtime may read only:

* Deployments
* ReplicaSets
* Pods
* Events

Permitted namespaces:

* The namespace supplied in the investigation objective

Permitted targets:

* The specified workload
* Pods and ReplicaSets owned by that workload
* Events associated with those resources

Cluster-wide collection is not permitted.

---

## Permitted Evidence

The allowed operations may collect:

* Deployment specification and status
* ReplicaSet specification and status
* Pod specification and status
* Container readiness state
* Readiness probe configuration
* Pod conditions
* Container restart information
* Kubernetes events related to the investigation target

The first workflow does not require access to Secrets, ConfigMaps, application logs, node data, or unrelated workloads.

---

## Forbidden Kubernetes Mutations

The OpenOps identity must not have permission to perform any mutating verb, including:

* `create`
* `update`
* `patch`
* `delete`
* `deletecollection`

OpenOps must not:

* Modify workload specifications
* Restart or delete Pods
* Scale workloads
* Change readiness probes
* Create debugging resources
* Apply manifests
* Perform remediation

Recommendations may be returned to the engineer, but OpenOps cannot execute them.

---

## Forbidden Execution Operations

OpenOps must not execute commands inside containers or nodes.

The following are forbidden:

* Pod `exec`
* Pod `attach`
* Ephemeral container creation
* Port forwarding
* Node shell access
* Host command execution
* Arbitrary `kubectl` command execution
* Shell subprocesses constructed by the model

The model may select only from predefined read-only tool contracts.

---

## Tool Enforcement

Each Kubernetes collector must map to a predefined operation with fixed authorization requirements.

The model may provide only validated parameters such as:

* cluster context
* namespace
* workload kind
* workload name

The model must not provide:

* Kubernetes verbs
* Arbitrary resource paths
* Shell commands
* Command-line flags
* Raw API requests

The tool adapter must reject operations outside the permitted resource and verb allowlist before contacting the Kubernetes API.

---

## Credential Boundary

OpenOps must use a dedicated Kubernetes identity.

That identity must:

* Have read-only access to the permitted resources
* Be restricted to the investigation namespace
* Have no mutation permissions
* Have no Pod execution permissions
* Have no access to Secrets
* Have no cluster-admin privileges

The runtime must not inherit broader permissions from the engineer's personal Kubernetes identity.

---

## Authorization Failure

If Kubernetes denies a requested read:

1. The collector returns a failed `ToolResult`.
2. `error_category` is set to `authorization`.
3. `retryable` is set to `false`.
4. OpenOps does not attempt a broader or alternative privileged operation.
5. The investigation continues only when the remaining permitted evidence is sufficient.

OpenOps must never respond to an authorization failure by escalating its own permissions.

---

## Boundary Invariant

Every Kubernetes interaction in the first workflow must satisfy all of the following:

* The verb is `get`, `list`, or `watch`.
* The resource is a Deployment, ReplicaSet, Pod, or Event.
* The resource belongs to the investigation namespace.
* The resource is the investigation target or is related to it.
* No shell or container execution is involved.
* No Kubernetes object is mutated.

Any operation that violates one of these conditions must be rejected before execution.
