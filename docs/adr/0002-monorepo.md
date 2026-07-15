# ADR 0002: Monorepo and Modular Monolith

## Status

Accepted

## Context

The first implementation is a single investigation workflow with tightly coupled components.

Introducing multiple repositories or independently deployable services would increase operational complexity without solving a current problem.

## Decision

OpenOps will be developed as a single monorepo.

The runtime will be one installable application in one repository. Source files may separate CLI intake, Kubernetes reads, schemas, normalization, decision, validation, and report rendering so each behavior can be tested directly.

This decision does not authorize a module framework, internal service layer, plugin boundary, or unused future package. Every source area must be exercised by the first workflow.

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
* Logical boundaries still require discipline to keep Kubernetes response formats out of decision code.

## Revisit Trigger

Revisit this decision if one or more independently deployable components emerge with measured operational or scaling requirements.

The decision must not be revisited based on anticipated future growth alone.
