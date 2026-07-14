# ADR 0002: Monorepo and Modular Monolith

## Status

Accepted

## Context

The first implementation is a single investigation workflow with tightly coupled components.

Introducing multiple repositories or independently deployable services would increase operational complexity without solving a current problem.

## Decision

OpenOps will be developed as a single monorepo.

The runtime will be implemented as a modular monolith composed of logical modules with explicit responsibilities.

Modules may evolve independently but are built, tested, and released as a single application.

## Alternatives Considered

### Multiple repositories

Rejected because repository boundaries do not yet exist.

### Microservices

Rejected because the first workflow has no scalability or deployment requirements that justify distributed services.

## Consequences

### Positive

* Single source of truth.
* Simple development workflow.
* Easy refactoring across modules.
* Shared contracts and tests.
* No distributed systems complexity.

### Negative

* The repository grows over time.
* Modules require discipline to avoid tight coupling.

## Revisit Trigger

Revisit this decision if one or more independently deployable components emerge with measured operational or scaling requirements.

The decision must not be revisited based on anticipated future growth alone.
