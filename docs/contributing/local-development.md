# Local Development

This is the canonical setup and quality-check guide for the Phase 2 walking skeleton.

## 1. Prerequisites

- Git
- `uv` 0.11.28
- Python 3.12, installed or managed by `uv`
- Docker, kubectl, and kind for later Phase 2 live work

On Windows, install the user-space tools with:

```powershell
winget install --id astral-sh.uv --exact --scope user
winget install --id Kubernetes.kubectl --exact --scope user
winget install --id Kubernetes.kind --exact --scope user
```

If Git is missing, Git for Windows can be installed separately with `winget install --id Git.Git --exact`; its installer may require administrator approval. Restart the shell after installation. Docker Engine must be installed in the same environment that will run `kind`; on the recorded workstation, Docker, kubectl, and kind run together in WSL.

For other operating systems, use the official [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/), [kubectl installation guide](https://kubernetes.io/docs/tasks/tools/), and [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/).

## 2. Clone the existing repository

```text
git clone https://github.com/Omerbirsh/OpenOps.git
cd OpenOps
```

## 3. Select Python 3.12

The repository's `.python-version` selects Python 3.12. Ensure it is available:

```text
uv python install 3.12
uv python find 3.12
```

## 4. Synchronize the locked environment

```text
uv sync --frozen --dev
```

This creates `.venv`, installs the editable `openops` package, and installs only the locked development tools. Do not introduce a second requirements or package-manager workflow.

## 5. Verify the package entry point

```text
uv run openops --help
```

The command documents the single synchronous `investigate` workflow. A real run requires the explicit reader context created by the [Phase 2 quick start](../user/quick-start.md).

## 6. Format and check formatting

Apply formatting:

```text
uv run ruff format .
```

Verify formatting without changes:

```text
uv run ruff format --check .
```

## 7. Lint

```text
uv run ruff check .
```

## 8. Type-check

```text
uv run mypy
```

## 9. Run deterministic tests

```text
uv run pytest
```

The default pytest configuration selects only tests marked `unit`. It requires no Docker daemon, Kubernetes cluster, network access, or provider credential. Unknown markers fail.

## 10. Select non-default test categories explicitly

```text
uv run pytest -m integration
uv run pytest -m live_cluster
uv run pytest -m live_model
```

Live tests remain opt-in and validate their prerequisites before contacting an external system. `live_model` performs three paid model calls; run it only against the disposable faulted lab.

## 11. Check for likely secrets

```text
uv run python scripts/check_secrets.py
```

The check scans tracked and untracked, non-ignored text files without online secret verification. It reports only file, line, and finding type, never the candidate value. Generated `uv.lock`, the roadmap PDF, and the documented public NGINX image-digest line are excluded for specific non-secret reasons.

## 12. Run the complete deterministic gate

```text
uv sync --frozen --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv run python scripts/check_secrets.py
```

CI runs these same commands.

## 13. Verify the Docker and Kubernetes workstation safely

Check tools without contacting a cluster:

```text
docker version
kubectl version --client
kind version
kubectl config current-context
kubectl config get-contexts -o name
```

Run all three tools in the same environment as Docker Engine. Docker Desktop or WSL are both supported when `kind` can reach the selected Docker daemon.

If Docker is installed, verify the daemon with one disposable container:

```text
docker run --rm hello-world
```

Do not issue a Kubernetes cluster request unless the selected context is the explicitly created local disposable context. Scenario tooling uses isolated administrative context `kind-openops-lab`; the runtime accepts only `openops-reader@kind-openops-lab`.

## Current limitations

- Only the exact broken-readiness target is accepted.
- Only Deployment, Pod, and Event evidence is collected.
- The runtime has no retries, persistence service, generic tool registry, shell path, writes, logs, or remediation.
- `OPENOPS_KUBECONFIG` selects the isolated reader kubeconfig, `OPENAI_API_KEY` authenticates the live model call, and `OPENOPS_MODEL` optionally overrides the documented default.

## Workstation readiness record

Last verified on 2026-07-19 on the Windows development workstation:

- Python 3.12.5 and uv 0.11.28 are available on Windows.
- Docker Engine 29.6.1, kubectl v1.36.1, and kind v0.32.0 are available together through Docker Desktop.
- The pinned Kubernetes v1.36.1 kind cluster, healthy baseline, single injected fault, reader RBAC denials, and live official-client collection were verified.
- The repository uses the public `Omerbirsh/OpenOps` origin over HTTPS. Local Git identity matches the existing repository author, and authenticated GitHub access has admin/push permission.
