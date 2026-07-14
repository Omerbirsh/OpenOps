# ADR 0001: Language and Packaging

## Status

Accepted

## Context

OpenOps needs an implementation stack for the first workflow.

The stack must support:

* Kubernetes API integration
* Structured data models
* Validation
* Deterministic tool contracts
* Fast local development
* Simple dependency management
* Straightforward testing

The current project is small and does not require a compiled language or a distributed runtime.

## Decision

OpenOps will use Python as its implementation language.

OpenOps will use `uv` for:

* Python version management
* Virtual environment creation
* Dependency installation
* Dependency locking
* Running project commands

Project metadata and dependencies will be defined in `pyproject.toml`.

The lock file produced by `uv` will be committed to the repository.

## Alternatives Considered

### Python with pip and venv

Rejected because it requires separate tools and conventions for environment creation, dependency installation, and reproducible locking.

### Python with Poetry

Rejected because `uv` provides the required packaging and environment capabilities with less tooling overhead and faster dependency operations.

### Go

Rejected for the first workflow because Python provides faster iteration for model integration, schema validation, and experimentation.

Go may become relevant later for performance-sensitive collectors, standalone binaries, or production runtime components.

### TypeScript

Rejected because the first workflow is backend and systems-oriented, and Python currently provides a stronger fit for Kubernetes automation, validation, and model-related development.

## Consequences

### Positive

* Fast implementation and iteration.
* Strong ecosystem for Kubernetes and model integrations.
* Structured validation can be implemented with Python libraries such as Pydantic.
* `uv` provides one tool for environment and dependency management.
* Locked dependencies make local and CI environments reproducible.

### Negative

* Python provides weaker compile-time guarantees than Go or Rust.
* Runtime type validation is required for critical contracts.
* Packaging a standalone executable may be less direct.
* Performance may become a constraint for large-scale or concurrent workloads.

## Reversibility

The decision is reversible because the architecture is defined through explicit contracts:

* `InvestigationState`
* `ToolResult`
* `EvidenceRecord`
* `FinalDiagnosis`

These contracts should remain independent of Python-specific behavior.

A future implementation in another language must preserve the same observable contracts and workflow boundaries.

## Revisit Trigger

Revisit this decision if one or more of the following become true:

* Python performance becomes a measured runtime bottleneck.
* The project requires a single portable static binary.
* Collector concurrency or memory usage becomes difficult to manage.
* Deployment constraints make the Python runtime impractical.
* The team operating the project standardizes on another language.
* Maintaining runtime validation becomes materially more complex than using stronger compile-time guarantees.

The decision must not be revisited based only on preference or speculative future scale.
