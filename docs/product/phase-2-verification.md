# Phase 2 Verification Record

Verified on 2026-07-19 against Docker Engine 29.6.1, kind v0.32.0, Kubernetes v1.36.1,
kubectl v1.36.1, Python 3.12.5, and uv 0.11.28.

## User acceptance criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Reproducible, read-only live kind scenario with one root cause | Pass | Two create/setup/fault cycles completed from an empty lab; reset restored health; reader reads succeeded while patch, delete, Secret, and exec checks were denied. |
| CLI collects real bounded evidence through the Kubernetes client | Pass | `tests/test_live_cluster.py` completed both the runtime and CLI paths against the faulted live cluster. |
| Schema-valid diagnosis with independently checked evidence IDs | Pass | The structured provider boundary supplies `FinalDiagnosis`; runtime validation rejects malformed, empty, duplicate, unknown, and non-visible references without retry or report. |
| Entire deterministic flow needs no cluster or model call | Pass | The default suite completes intake, three fixture collectors, normalization, fake decision, validation, report, failure paths, and trace checks. |
| Sanitized trace and reproducible quick start | Pass | `docs/demonstrations/broken-readiness-trace.json` came from live Kubernetes collection and contains no raw data or credentials; `docs/user/quick-start.md` covers create through teardown. |
| Green main with no future platform layer | Pass when merged | Scope audit found no service, database, tool registry, planner, application logs, shell runtime, Kubernetes writes, or remediation path. |

## Executed gates

- `uv sync --frozen --dev`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy`
- `uv run pytest`
- `uv run pytest -m live_cluster` with `OPENOPS_LIVE_CLUSTER=1`
- `uv run python scripts/check_secrets.py`
- scenario `create`, `setup`, `fault`, `verify-fault`, `verify-rbac`, `reset`, and `teardown`

The paid `live_model` marker is intentionally opt-in and requires `OPENAI_API_KEY`. It performs three
unchanged live runs and checks semantic equivalence. No provider credential was available in the
verification environment, so that external gate was not executed here; the same one-call SDK boundary
is covered deterministically with a schema-parsing client double.
