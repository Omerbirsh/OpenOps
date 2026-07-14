# InvestigationState v0

`InvestigationState` is the single in-memory record of one investigation. Intake validation happens before state creation. The runtime owns state transitions and list appends.

## Fields

| Field | Type | Lifecycle |
| --- | --- | --- |
| `objective` | validated investigation objective | Copied once from intake and never modified. |
| `phase` | enum | Runtime-owned: `collecting`, `deciding`, or `finished`. |
| `status` | enum | Runtime-owned: `running`, `completed`, or `failed`. |
| `tool_results` | list of `ToolResult` | Append-only; one entry for every attempted collector execution. |
| `evidence` | list of `EvidenceRecord` | Append-only; populated by deterministic normalization after collection. |
| `decision` | `FinalDiagnosis` or null | Null until a candidate passes validation; then written once by the runtime. |
| `limits` | fixed execution limits | Set at creation and never modified. |
| `failure` | failure summary or null | Set only when status becomes `failed`. |

The objective fields are defined in [intake.md](../product/intake.md). `ToolResult`, `EvidenceRecord`, and `FinalDiagnosis` are defined in their respective architecture contracts.

## Fixed limits

| Limit | v0 value |
| --- | --- |
| `max_tool_executions` | 3 |
| `max_tool_result_bytes` | 64 KiB per result |
| `max_event_items` | 20 |
| `max_evidence_records` | 20 |
| `max_model_calls` | 1 |
| `max_model_output_tokens` | 1,000 |

These are safety bounds, not planning controls. They are constants for v0 rather than user configuration.

## State transitions

The only successful path is:

```text
collecting/running
    -> deciding/running
    -> finished/completed
```

Any runtime failure produces:

```text
<current phase>/running
    -> finished/failed
```

There is no transition from `finished`, no return from `deciding` to `collecting`, and no retry loop.

## Collection and evidence rules

- The runtime attempts the three collectors once in their fixed order.
- Each returned result is appended before any normalization.
- After all three attempts, the normalizer processes stored results in the same order.
- Existing results and evidence records are immutable.
- If normalization produces no evidence, the investigation fails without a model call.
- Partial and failed results are retained and later rendered as collection warnings when a report can still be completed.

## Failure summary

`failure` contains:

- `stage`: `collection`, `normalization`, `model`, or `validation`;
- `category`: a bounded machine-readable value; and
- `message`: a safe human-readable summary without credentials, raw object content, or stack traces.

The state is not persisted in v0. A future persistence design must not be inferred from this in-memory contract.
