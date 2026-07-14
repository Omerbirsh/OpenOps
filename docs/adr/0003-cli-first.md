# ADR 0003: CLI-First Interface

## Status

Accepted

## Context

The first users of OpenOps are engineers.

The initial workflow requires only a way to start an investigation and receive a structured report.

A service API or web interface would increase implementation effort without improving the first workflow.

## Decision

OpenOps will expose a command-line interface as its primary interface.

The CLI is the only supported entry point for the first implementation.

No REST API, gRPC service, or web interface will be developed in this milestone.

## Alternatives Considered

### REST API

Rejected because there are no external consumers requiring service integration.

### Web Interface

Rejected because visualization is not required to validate the investigation workflow.

## Consequences

### Positive

* Small implementation surface.
* Fast development.
* Easy local testing.
* Natural workflow for engineers.

### Negative

* No remote access.
* No browser interface.
* External integrations must wait.

## Review Gate

A service interface may be considered only after the CLI workflow can consistently:

* complete an investigation,
* produce a validated diagnosis,
* satisfy the acceptance checklist,
* and demonstrate value through real usage.

The interface must not change before the investigation workflow is proven.
