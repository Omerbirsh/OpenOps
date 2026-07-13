# OpenOps Product Charter

## Product Boundary

OpenOps is an evidence-driven operations investigation runtime that collects operational evidence, preserves its provenance, and produces traceable diagnoses with explicit uncertainty.

It is not a generic AI chatbot, coding assistant, or general-purpose DevOps copilot.

---

## Flagship User and Investigation Trigger

The flagship user is an operations engineer investigating an unhealthy Kubernetes workload.

An investigation starts with:

- Cluster context
- Namespace
- Workload kind
- Workload name
- Observed symptom

These inputs define the investigation target.

---

## First Scenario Scope

The first supported scenario is a Kubernetes Deployment whose Pods fail to become Ready because of a broken readiness probe.

The investigation runs against a reproducible local Kubernetes cluster using Kubernetes-native evidence only.

No additional incident scenarios, external integrations, remediation, web interface, API service, database, or multi-agent workflow are included in this scope.