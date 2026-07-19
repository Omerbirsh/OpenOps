# Broken Readiness Scenario

This directory implements the disposable `kind` lab defined by the
[scenario specification](../../docs/scenarios/broken-readiness.md). The lifecycle tool always names
the `openops-lab` cluster and always uses an isolated administrative kubeconfig under the ignored
`.openops-lab/` directory.

The node image is pinned to the digest published for kind v0.32.0. The workload image and all
scenario identities are pinned by the scenario contract.

## Lifecycle

Run from the repository root:

```text
uv run python scenarios/broken-readiness/manage.py create
uv run python scenarios/broken-readiness/manage.py setup
uv run python scenarios/broken-readiness/manage.py fault
uv run python scenarios/broken-readiness/manage.py verify-fault
uv run python scenarios/broken-readiness/manage.py verify-rbac
uv run python scenarios/broken-readiness/manage.py reset
uv run python scenarios/broken-readiness/manage.py teardown
```

`create` creates only the cluster. `setup` installs and verifies the healthy workload and creates a
short-lived, reader-only kubeconfig at `.openops-lab/kubeconfig`. `fault` changes only the readiness
path from `/` to `/ready`, then proves that the process is running, the Pod is unready with zero
restarts, and Kubernetes reports readiness HTTP 404. `reset` restores the healthy probe. `teardown`
deletes only the named disposable cluster and its local credentials.

The lifecycle tool may mutate this disposable lab through the administrative context. It is not part
of the `openops` package or runtime. OpenOps accepts only `openops-reader@kind-openops-lab` and has
no mutation or shell path.
