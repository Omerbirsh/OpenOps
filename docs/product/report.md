# Human-Readable Report Contract v0

A completed investigation renders one terminal report from the validated `FinalDiagnosis`, its cited `EvidenceRecord` objects, and any collection warnings. A candidate diagnosis is never rendered.

## Required sections

1. **Target** - cluster context, namespace, workload kind, and workload name.
2. **Reported symptom** - the intake symptom, labeled as user-provided context rather than collected evidence.
3. **Diagnosis** - `cause` and `confidence`.
4. **Cited evidence** - for every `evidence_id`, the matching evidence ID, observation, source collector, and target.
5. **Alternatives or uncertainty** - every value from `alternatives`; render `None stated` when the list is empty.
6. **Recommendation** - the non-executed next action.
7. **Collection warnings** - failed, partial, or truncated `ToolResult` summaries; render `None` when absent.

The report must resolve evidence IDs to readable evidence. Showing IDs without their observations is not sufficient traceability.

## Failure behavior

If collection produces no evidence, the model call fails, or the candidate diagnosis fails validation, the investigation ends as failed. The CLI prints a bounded error summary and does not render a diagnosis report.

The v0 deliverable is human-readable terminal output. A JSON report mode is not required by the current contract.
