# Local Development

This is the canonical Phase 1 setup and quality-check guide. The Kubernetes investigator is not implemented yet; these steps install and validate only the repository foundation.

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
uv run openops
```

The command currently prints that the investigation runtime is not implemented and exits with code 2. That is intentional in Phase 1; it proves packaging without advertising a false capability.

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

Phase 1 contains no tests in these categories. Future live tests must remain opt-in and must validate their own prerequisites before contacting an external system.

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

Run those commands inside WSL when using the recorded Windows/WSL setup. From PowerShell, prefix each command with `wsl --`, for example `wsl -- docker version` and `wsl -- kind version`.

If Docker is installed, verify the daemon with one disposable container:

```text
docker run --rm hello-world
```

Do not issue a Kubernetes cluster request unless the selected context is an explicitly created local disposable context. Phase 2 will create administrative context `kind-openops-lab` and separate read-only runtime context `openops-reader@kind-openops-lab`; neither exists as part of Phase 1.

## Current limitations

- No investigation schemas, collectors, model integration, scenario manifests, or functional investigation CLI exist yet.
- No environment variables are consumed.
- No live test is implemented.
- The Phase 1 runtime dependency set is intentionally empty because the install/CLI smoke path uses only the Python standard library. Add Pydantic, the Kubernetes client, a CLI library, or a provider SDK only in the phase that adds code importing it.

## Workstation readiness record

Last verified on 2026-07-16 on the Windows development workstation:

- Python 3.12.5 and uv 0.11.28 are available on Windows.
- WSL has Docker Engine 29.3.1, kubectl v1.36.2, and kind v0.32.0. A disposable `hello-world` container ran successfully, and `kind get clusters` reached Docker successfully.
- No Kubernetes context is selected and no kind clusters exist, so automation cannot accidentally target an existing cluster.
- The repository uses the public `Omerbirsh/OpenOps` origin over HTTPS. Local Git identity matches the existing repository author, and authenticated GitHub access has admin/push permission.
