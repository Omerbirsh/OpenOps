# OpenOps

OpenOps is an evidence-driven operations investigation runtime. It is intended to collect bounded operational evidence, normalize tool-specific output into traceable facts, and produce evidence-linked diagnoses with explicit uncertainty.

## Current status

Phase 0 architecture, the Phase 1 repository foundation, and the bounded Phase 2 walking skeleton are implemented. OpenOps can reproduce one broken-readiness incident in a disposable `kind` cluster, collect allowlisted Deployment/Pod/Event evidence through the official Kubernetes client, make one structured model call, independently validate evidence IDs, and render a cited report.

The default test suite runs the entire workflow with fixtures and a fake provider, without a cluster, network, or paid model call. Live-cluster and live-model checks are explicit opt-in gates. OpenOps remains a fixed local demonstration, not a general Kubernetes investigator or production-ready system.

## Implemented boundary

The first implementation is deliberately fixed:

- one local `kind` cluster;
- one namespace and one Deployment;
- one broken HTTP readiness-probe scenario;
- three read-only Kubernetes collectors executed in a fixed sequence;
- deterministic evidence normalization;
- one model call after collection;
- mechanical schema and evidence-reference validation;
- one human-readable report with cited evidence;
- no remediation.

The model does not select tools, construct Kubernetes requests, or control collection.

## Development setup

With `uv` 0.11.28 available:

```text
uv python install 3.12
uv sync --frozen --dev
uv run pytest
```

See [Local development](docs/contributing/local-development.md) for the complete setup, quality gate, marker policy, and safe workstation checks.

For the disposable lab and first real investigation, follow the [Phase 2 quick start](docs/user/quick-start.md).

## Documentation

- [Product charter](docs/product/charter.md)
- [First-workflow architecture](docs/architecture/overview.md)
- [Security boundary](docs/architecture/security/security-boundary.md)
- [Threat model](docs/architecture/security/threat-model.md)
- [Reference scenario](docs/scenarios/broken-readiness.md)
- [Acceptance criteria](docs/product/acceptance.md)
- [Phase 2 verification record](docs/product/phase-2-verification.md)
- [Non-goals](docs/product/non-goals.md)
- [Deferred capabilities](docs/planning/deferred.md)
- [Long-term vision](docs/vision.md)

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.

## Source of truth

The Markdown documents under `docs/` define the current v0 contracts. `BuildingRoadMap.pdf` is planning context and contains earlier assumptions, including same-day application-log collection, that are superseded by the narrower current contracts. Application logs remain deferred for v0.
