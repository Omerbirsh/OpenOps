# FinalDiagnosis v0

`FinalDiagnosis` is the structured conclusion produced by the decision stage.

It must be validated before being stored in `InvestigationState.decision` or returned in the final report.

---

## cause

Purpose: States the most likely root cause of the incident.

Type: Non-empty string.

Lifecycle Owner: Written by the decision stage.

Rules:

* Must describe one concrete cause.
* Must not present speculation as confirmed fact.
* Must be supported by the referenced evidence.

---

## confidence

Purpose: Expresses how strongly the available evidence supports the diagnosis.

Type: Enumeration.

Values:

* low
* medium
* high

Lifecycle Owner: Written by the decision stage.

Rules:

* `high` requires direct and consistent supporting evidence.
* `medium` means the evidence supports the cause but meaningful uncertainty remains.
* `low` means the cause is plausible but weakly supported.

---

## evidence_ids

Purpose: Identifies the evidence records supporting the diagnosis.

Type: Non-empty list of unique evidence ID strings.

Lifecycle Owner: Written by the decision stage.

Rules:

* Every value must match an existing `EvidenceRecord.id` in `InvestigationState.evidence`.
* Unsupported or unknown evidence IDs are invalid.
* Duplicate evidence IDs are invalid.
* The diagnosis must not reference `ToolResult` objects directly.
* At least one evidence ID is required.
* Every cited evidence record must materially support the stated cause.

---

## alternatives

Purpose: Records other plausible causes or unresolved uncertainty.

Type: List of strings.

Lifecycle Owner: Written by the decision stage.

Rules:

* May be empty only when the evidence supports the cause with high confidence and no meaningful uncertainty remains.
* Alternatives must not contradict confirmed evidence.
* Each entry must describe a distinct plausible explanation or unresolved limitation.

---

## recommendation

Purpose: Provides the next action the engineer should take.

Type: Non-empty string.

Lifecycle Owner: Written by the decision stage.

Rules:

* Must be directly related to the diagnosed cause.
* Must be actionable by an engineer.
* Must not perform remediation automatically.
* Must not recommend unsupported changes.

---

## Validation Rules

A `FinalDiagnosis` is valid only when all of the following are true:

* `cause` is present and non-empty.
* `confidence` is one of the allowed values.
* `evidence_ids` contains at least one unique ID.
* Every evidence ID exists in `InvestigationState.evidence`.
* Every cited evidence record supports the diagnosis.
* `alternatives` is present, even when empty.
* `recommendation` is present and non-empty.
* No conclusion depends directly on unnormalized tool output.

If any validation rule fails, the diagnosis must not be stored or returned as a completed investigation result.
