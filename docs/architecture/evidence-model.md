# EvidenceRecord v0

An `EvidenceRecord` represents a single observation collected during an investigation.

Every piece of evidence has a stable identity, records where it came from, and preserves enough metadata for the final diagnosis to reference it without ambiguity.

---

## id

Purpose: Uniquely identifies the evidence within an investigation.

Type: Unique identifier.

Lifecycle Owner: Assigned by the evidence normalization stage.
Never changes.

---

## source_tool

Purpose: Records which tool produced the evidence.

Type: Tool identifier.

Examples

- kubectl_get_pods
- kubectl_describe_pod
- kubectl_get_events

Lifecycle Owner: Assigned by the evidence normalization stage.
Never changes.

---

## timestamp

Purpose: Records when the evidence was collected.

Type: Timestamp.

Lifecycle Owner: Assigned by the evidence normalization stage.
Never changes.

---

## target

Purpose: Identifies the Kubernetes resource the evidence refers to.

Type: Structured target reference.

Contains:
- cluster_context
- namespace
- resource_kind
- resource_name

Lifecycle Owner: Assigned by the evidence normalization stage.
Never changes.

---

## observation

Purpose: Stores the normalized factual observation extracted from the tool output.

Type: Text.

Examples

- Readiness probe failed with HTTP 404.
- Pod is Running but 0/1 Ready.

Lifecycle Owner: Written by the evidence normalization stage.
Never changes.

---

## sensitivity

Purpose: Classifies whether the evidence contains sensitive information.

Type: Enumeration.

Values
- public
- internal
- sensitive

Lifecycle Owner: Assigned by the evidence normalization stage.

---

## raw_reference

Purpose: Points to the original tool output from which the observation was derived.

Type: Reference metadata.

Examples
- Stored stdout and stderr artifact path
- Preserved Kubernetes API response location
- Raw command output artifact identifier
- Log output location

Lifecycle Owner: Assigned by the evidence normalization stage.
Never changes.