# Phase 2 Quick Start

This walkthrough reproduces the only supported investigation: one `readiness-demo` Deployment in
the disposable `openops-lab` kind cluster. It never points OpenOps at an implicit Kubernetes context.

## 1. Install and verify

From the repository root:

```text
uv sync --frozen --dev
uv run pytest
uv run ruff check .
uv run mypy
```

Docker, kind v0.32.0 or newer, and kubectl must be available in the same environment.

## 2. Create the lab and prove the healthy baseline

```text
uv run python scenarios/broken-readiness/manage.py create
uv run python scenarios/broken-readiness/manage.py setup
```

`setup` verifies the healthy Deployment and proves that the reader can perform the three required
reads while Deployment patch, Pod deletion, Secret reads, and Pod exec are denied. It writes a
short-lived, reader-only kubeconfig to the ignored `.openops-lab/kubeconfig` file.

## 3. Inject and verify the one root cause

```text
uv run python scenarios/broken-readiness/manage.py fault
```

The command changes only `readinessProbe.httpGet.path` from `/` to `/ready`. It passes only after
Kubernetes shows a Running-but-unready Pod with zero restarts, zero available Deployment replicas,
and an `Unhealthy` readiness Event reporting HTTP 404.

## 4. Run the real CLI

Set configuration in the current shell. PowerShell:

```powershell
$env:OPENOPS_KUBECONFIG = (Resolve-Path ".openops-lab/kubeconfig").Path
$env:OPENAI_API_KEY = "<set locally; never commit it>"
```

Bash:

```bash
export OPENOPS_KUBECONFIG="$PWD/.openops-lab/kubeconfig"
export OPENAI_API_KEY="<set locally; never commit it>"
```

Then run one investigation:

```text
uv run openops investigate --cluster-context openops-reader@kind-openops-lab --namespace openops-lab --workload-kind Deployment --workload-name readiness-demo --symptom "Pod is Running but not Ready" --trace-file .openops-lab/trace-1.json
```

The trace contains normalized evidence and collector summaries only. It excludes kubeconfig data,
tokens, raw Kubernetes objects, full Event messages, and raw references. OpenOps refuses to overwrite
an existing trace path.

## 5. Run the opt-in live gates

PowerShell:

```powershell
$env:OPENOPS_LIVE_CLUSTER = "1"
uv run pytest -m live_cluster
$env:OPENOPS_LIVE_MODEL = "1"
uv run pytest -m live_model
```

The live-model test makes three paid model calls against an unchanged scenario and checks semantic
equivalence, high confidence, the `/ready`/404 cause, and all three required evidence categories.

## 6. Reset or remove the lab

```text
uv run python scenarios/broken-readiness/manage.py reset
uv run python scenarios/broken-readiness/manage.py teardown
```

`reset` proves the healthy baseline again. `teardown` deletes only the explicitly named
`openops-lab` cluster and the ignored local lab credentials.
