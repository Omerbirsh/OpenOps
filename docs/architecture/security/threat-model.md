# v0 Threat Model

This threat model covers only the fixed local Kubernetes investigation. Kubernetes objects, Event messages, collector failures, and model output are untrusted.

## 1. Excessive Kubernetes authority

**Risk:** A runtime using the administrative `kind` context or a broad identity could mutate the cluster or read unrelated data.

**Current controls:**

- the CLI accepts only `openops-reader@kind-openops-lab`;
- a namespace Role allows only required Deployment, Pod, and Event reads;
- runtime code has no write, exec, log, port-forward, shell, or generic-request path;
- tests verify allowed reads and representative denied operations.

**Residual risk:** Kubernetes RBAC cannot constrain Pod/Event list results to one owner. Fixed selectors, UID filtering, and allowlisted serialization enforce that narrower data boundary in the adapter.

**Deferred:** automated RBAC auditing and policy generation.

## 2. Credential disclosure

**Risk:** Kubernetes or model-provider credentials enter tool output, prompts, errors, reports, traces, or source control.

**Current controls:**

- clients load credentials internally from explicit configuration;
- credentials are not contract fields and are never serialized into investigation state;
- adapters create bounded error categories instead of copying raw exceptions;
- only normalized evidence enters model context;
- v0 does not persist raw output.

**Deferred:** generalized secret scanning, dedicated secret storage, and automatic redaction for additional evidence sources.

## 3. Prompt injection or misleading Kubernetes text

**Risk:** An annotation, label, or Event message contains instructions or fabricated operational guidance intended to influence the model.

**Current controls:**

- complete objects are never sent to the model;
- annotations and arbitrary labels are excluded;
- normalization is deterministic application code;
- the Event normalizer emits a controlled fact only for recognized readiness metadata and an extracted HTTP status code;
- complete Event messages remain outside model context;
- the model cannot change collection or invoke an action even if diagnosis quality is affected.

**Deferred:** generic injection detection and sanitization for future free-text evidence such as logs.

## 4. Oversized or noisy Kubernetes output

**Risk:** Large lists or objects exhaust memory, overflow model context, or hide relevant evidence.

**Current controls:**

- collectors select fields before storing results;
- each `ToolResult` is limited to 64 KiB;
- Events are filtered to target UIDs, bounded to 20, and message text is capped at 512 characters;
- normalization is capped at 20 evidence records;
- raw result data is never included in model context.

**Deferred:** streaming, chunking, and summarization, which are unnecessary for the fixed one-replica lab.

## 5. Fabricated or malformed diagnosis

**Risk:** The model returns invalid structure, cites nonexistent evidence, or states an unsupported cause confidently.

**Current controls:**

- structured output is mechanically validated;
- empty, duplicate, unknown, and non-model-visible evidence references are rejected;
- an invalid candidate fails closed without a retry or report;
- deterministic fixtures test validator behavior;
- the known scenario evaluates cause, confidence, evidence coverage, and recommendation quality across repeated runs.

**Residual risk:** Evidence-ID validation proves provenance, not semantic correctness. Scenario evaluation, not the schema validator, measures grounding quality.

**Deferred:** broader evaluation suites, cross-source scoring, and confidence calibration across multiple scenarios.

## Security invariants

- The model never operates Kubernetes.
- The runtime never uses an implicit or administrative kube context.
- Kubernetes credentials never enter model context or investigation data.
- Only allowlisted normalized evidence enters model context.
- Every cited evidence ID must exist in the current investigation.
- No output from OpenOps performs or authorizes remediation.
