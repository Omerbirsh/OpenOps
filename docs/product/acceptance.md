# v0 Acceptance Criteria

The first implementation is complete only when every required check below passes. A single successful model response is not sufficient.

## Deterministic checks without a cluster or live model

- [ ] Intake accepts the exact v0 target and rejects other contexts, namespaces, workload kinds, and workload names before external calls.
- [ ] Fixture-backed collectors execute in the documented order: Deployment, Pods, Events.
- [ ] Every attempted collector execution produces one stored `ToolResult`, including failures and partial results.
- [ ] Normalization produces a stable ordered evidence set from the same fixture input.
- [ ] Evidence records cite an existing `ToolResult` through `raw_reference`.
- [ ] The model context contains the objective and normalized evidence only; it contains no credentials, complete Kubernetes objects, raw event messages, or `ToolResult` objects.
- [ ] A fake model provider is called exactly once.
- [ ] The validator rejects malformed diagnoses, empty evidence lists, duplicate evidence IDs, and unknown evidence IDs.
- [ ] The report resolves every cited evidence ID to its corresponding observation.
- [ ] Collection, model, and validation failures end with `status: failed` and do not render a diagnosis report.
- [ ] No runtime path can perform Kubernetes writes, execute shell commands, or execute commands in Pods or nodes.

## Live reference-scenario checks

- [ ] A local cluster named `openops-lab` has administrative context `kind-openops-lab` and a separate runtime context named `openops-reader@kind-openops-lab`.
- [ ] The `openops-lab` namespace contains the exact scenario from `docs/scenarios/broken-readiness.md`.
- [ ] The application process is running, the Pod phase is `Running`, the container restart count is zero, and the Pod is not Ready.
- [ ] The Deployment reports zero available replicas.
- [ ] Kubernetes reports a readiness-probe HTTP 404 failure for the target Pod.
- [ ] The runtime identity can perform the required Deployment, Pod, and Event reads and is denied create, update, patch, delete, exec, and secret reads.
- [ ] A live run collects real Kubernetes evidence through the official client and makes one model call after collection.
- [ ] The validated diagnosis identifies the readiness probe at path `/ready` returning HTTP 404 as the cause of the Pod remaining unready.
- [ ] The report uses `high` confidence, cites the probe configuration, Pod readiness state, and readiness-failure Event evidence, and recommends aligning the readiness probe with an endpoint that returns success.
- [ ] OpenOps performs no remediation.

## Repeatability

Three consecutive live runs against an unchanged scenario pass when they are semantically equivalent:

- the diagnosed cause is the broken readiness-probe path;
- confidence is `high`;
- each report cites evidence covering probe configuration, Pod readiness, and the HTTP 404 probe failure;
- no unsupported evidence ID appears; and
- no prohibited action is attempted.

Pod names, collection timestamps, durations, and run-local evidence IDs may differ and are not part of semantic equivalence.

## Phase 0 completion gate

Phase 0 is complete when the Markdown contracts are mutually consistent, the scenario has one exact ground truth, and no future component is required to explain the first run. Implementation and live checks belong to the following phases.
