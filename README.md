# OpenOps

OpenOps is an evidence-driven operations investigation runtime. It collects operational evidence, normalizes tool-specific output into traceable facts, and asks a decision model to diagnose only from those facts.

The repository is currently at the end of Phase 0: documentation and architecture are defined, but the runtime is not yet implemented or usable.

## First implementation

The first implementation is deliberately fixed:

- one CLI;
- one local `kind` cluster;
- one namespace and one Deployment;
- one broken HTTP readiness-probe scenario;
- three read-only Kubernetes collectors executed in a fixed sequence;
- deterministic evidence normalization;
- one model call after collection;
- mechanical schema and evidence-reference validation;
- one human-readable report with cited evidence;
- no remediation.

The model does not select tools, construct Kubernetes requests, or control the collection flow.

## Documentation

- [Product charter](docs/product/charter.md)
- [First-workflow architecture](docs/architecture/overview.md)
- [Reference scenario](docs/scenarios/broken-readiness.md)
- [Acceptance criteria](docs/product/acceptance.md)
- [Security boundary](docs/architecture/security/security-boundary.md)
- [Non-goals](docs/product/non-goals.md)
- [Long-term vision](docs/vision.md)

## Source of truth

The Markdown documents under `docs/` define the current v0 contracts. `BuildingRoadMap.pdf` is planning context and contains earlier assumptions, including same-day application-log collection, that are superseded by the narrower current contracts. Application logs remain deferred for v0.
