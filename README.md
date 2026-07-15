# OpenOps

OpenOps is an evidence-driven operations investigation runtime. It is intended to collect bounded operational evidence, normalize tool-specific output into traceable facts, and produce evidence-linked diagnoses with explicit uncertainty.

## Current status

Phase 0 architecture and the Phase 1 repository/development foundation are complete. The Python package installs and exposes a deliberately nonfunctional console entry point, and deterministic formatting, linting, typing, unit-test, secret-check, and CI commands are configured. Docker, kubectl, and kind are verified together in WSL for the later disposable-cluster workflow.

The Kubernetes investigation runtime is **not implemented or usable yet**. There are no collectors, model integration, scenario manifests, general Kubernetes diagnosis, or remediation capabilities. The project is not production-ready.

## First implementation target

The first implementation remains deliberately fixed:

- one local `kind` cluster;
- one namespace and one Deployment;
- one broken HTTP readiness-probe scenario;
- three read-only Kubernetes collectors executed in a fixed sequence;
- deterministic evidence normalization;
- one model call after collection;
- mechanical schema and evidence-reference validation;
- one human-readable report with cited evidence;
- no remediation.

The model will not select tools, construct Kubernetes requests, or control collection.

## Development setup

With `uv` 0.11.28 available:

```text
uv python install 3.12
uv sync --frozen --dev
uv run pytest
```

See [Local development](docs/contributing/local-development.md) for the complete setup, quality gate, marker policy, and safe workstation checks.

## Documentation

- [Product charter](docs/product/charter.md)
- [First-workflow architecture](docs/architecture/overview.md)
- [Security boundary](docs/architecture/security/security-boundary.md)
- [Threat model](docs/architecture/security/threat-model.md)
- [Reference scenario](docs/scenarios/broken-readiness.md)
- [Acceptance criteria](docs/product/acceptance.md)
- [Non-goals](docs/product/non-goals.md)
- [Deferred capabilities](docs/planning/deferred.md)
- [Long-term vision](docs/vision.md)

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Source of truth

The Markdown documents under `docs/` define the current v0 contracts. `BuildingRoadMap.pdf` is planning context and contains earlier assumptions, including same-day application-log collection, that are superseded by the narrower current contracts. Application logs remain deferred for v0.
