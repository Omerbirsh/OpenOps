# OpenOps Product Charter

## Product Boundary

OpenOps is an evidence-driven operations investigation runtime that collects operational evidence, preserves its provenance, and produces traceable diagnoses with explicit uncertainty.

## Flagship User and Investigation Trigger

The flagship user is a NOC, SRE, DevOps, platform, or operations engineer investigating an unhealthy Kubernetes workload.

The engineer starts an investigation by providing:

- Kubernetes cluster context
- Namespace
- Workload kind
- Workload name
- Observed symptom

These inputs identify the operational target and provide the initial objective for the investigation.

## First Scenario Scope 

The first scenario is intentionaly simple; a Kubernetes Deployment whose Pods fail to become Ready because of a broken readiness probe.

The investigation will run against a reproducible local Kubernetes cluster and use Kubernetes-native evidence only.

No additional incident scenarios, external integrations, remediation capabilities, web interface, API service, database, or multi-agent workflow are included in the initial scope.



