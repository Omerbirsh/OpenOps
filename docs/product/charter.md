# OpenOps Product Charter

## Product boundary

OpenOps is an evidence-driven operations investigation runtime. It collects bounded operational evidence, preserves provenance, normalizes source-specific output into factual observations, and produces a structured diagnosis with explicit uncertainty and evidence citations.

It is not a generic AI chatbot, coding assistant, or general-purpose DevOps copilot.

## Flagship user

The first user is an operations engineer investigating a Kubernetes Deployment whose Pod is running but not Ready.

## First implementation objective

Given a validated target in the reference `kind` cluster, OpenOps must:

1. execute three predefined read-only Kubernetes collectors in a fixed sequence;
2. store every collector execution as a `ToolResult`;
3. deterministically normalize usable results into `EvidenceRecord` objects;
4. send only the objective and bounded normalized evidence to one decision model;
5. mechanically validate the returned `FinalDiagnosis` and its evidence IDs; and
6. render a human-readable report containing the diagnosis and the cited evidence.

The first scenario is one Deployment with one intentionally incorrect HTTP readiness-probe path. Collection is deterministic. The model does not select tools or cause additional collection.

## Current environment

The v0 target is fixed to:

- cluster type: local `kind`;
- cluster name: `openops-lab`;
- administrative cluster context: `kind-openops-lab` (scenario setup only);
- runtime read-only context: `openops-reader@kind-openops-lab`;
- namespace: `openops-lab`;
- workload kind: `Deployment`;
- workload name: `readiness-demo`.

The exact scenario is defined in [broken-readiness.md](../scenarios/broken-readiness.md).

## Completion boundary

The slice ends when a validated report is rendered. OpenOps may recommend a next action, but it cannot perform that action. Additional scenarios, application logs, external integrations, persistence, services, adaptive planning, and remediation are outside this implementation.
