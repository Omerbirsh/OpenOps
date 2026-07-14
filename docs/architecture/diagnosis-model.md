# FinalDiagnosis v0

`FinalDiagnosis` is the structured candidate returned by the one decision-model call. It becomes final only after deterministic validation against `InvestigationState.evidence`.

## Fields

| Field | Type | Rule |
| --- | --- | --- |
| `cause` | string, 1-1,000 characters | States one most likely cause. |
| `confidence` | enum | `low`, `medium`, or `high`. |
| `evidence_ids` | non-empty list of strings | Unique IDs of supporting `EvidenceRecord` objects. |
| `alternatives` | list of 0-5 strings, each 1-500 characters | Other plausible causes or unresolved uncertainty; present even when empty. |
| `recommendation` | string, 1-1,000 characters | A next action for an engineer; OpenOps does not execute it. |

The decision model may receive only the immutable objective, normalized model-visible evidence, the output schema, and bounded diagnosis instructions. It must not receive `ToolResult`, `raw_reference`, raw Kubernetes objects, credentials, or collection controls.

## Mechanical validation

The validator is application code. It performs only checks that can be determined without another model call:

1. all five fields are present with the declared types;
2. string and list lengths satisfy the declared bounds after trimming;
3. `confidence` is an allowed value;
4. `evidence_ids` is non-empty and contains no duplicates;
5. every evidence ID exists in `InvestigationState.evidence`; and
6. every cited record is model-visible (`sensitivity: internal`).

If any check fails:

- the candidate is discarded;
- `InvestigationState.decision` remains null;
- no second model call is made;
- the investigation finishes with `status: failed`; and
- no diagnosis report is rendered.

If all checks pass, the runtime writes the diagnosis once to `InvestigationState.decision`.

## Behavioral expectations and evaluation

Whether the cause is actually supported by the cited evidence, whether confidence is calibrated, and whether the recommendation is appropriate are quality properties. They are tested against the known scenario and fixtures; they are not falsely presented as deterministic schema validation.

For the reference scenario, acceptance requires a high-confidence diagnosis that attributes the unready Pod to the HTTP readiness probe at `/ready` returning 404, cites probe configuration, Pod readiness, and Event evidence, and recommends aligning the probe with a successful endpoint without performing remediation.
