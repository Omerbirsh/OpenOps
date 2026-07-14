# ToolResult v0

`ToolResult` is the immutable record of one collector execution. It records execution and bounded collector output; it is not evidence and must not contain a diagnosis.

The runtime appends a `ToolResult` to `InvestigationState.tool_results` immediately after each collector returns and before normalization begins.

## Fields

| Field | Type | Owner and rule |
| --- | --- | --- |
| `id` | string | Runtime-assigned, unique within the investigation. Fixed execution order makes `tool-001`, `tool-002`, and `tool-003` sufficient for v0. |
| `source_tool` | enum | Collector-assigned: `kubernetes_deployment`, `kubernetes_pods`, or `kubernetes_events`. |
| `collected_at` | timestamp | Collector completion time in UTC. |
| `status` | enum | `success`, `partial`, or `failure`. |
| `data` | collector-specific structured data or null | Bounded, allowlisted Kubernetes response fields. This is raw relative to evidence normalization, not a complete SDK object. |
| `raw_reference` | string or null | Runtime-created reference to this result's preserved `data`; see below. |
| `error_category` | enum or null | `invalid_input`, `authentication`, `authorization`, `not_found`, `timeout`, `unavailable`, `malformed_response`, or `execution_error`. |
| `error_message` | string up to 512 characters or null | Safe summary for the engineer. It must not contain credentials, kubeconfig content, response bodies, stack traces, or arbitrary exception representations. |
| `retryable` | boolean | Collector classification only. The v0 runtime does not retry automatically. |
| `duration_ms` | non-negative integer | Complete collector execution duration. |
| `truncated` | boolean | Whether collector output was omitted to satisfy the output limit. |

## Status invariants

### Success

- `status` is `success`.
- `data` is present.
- `error_category` and `error_message` are null.
- `retryable` is false.

### Partial

- `status` is `partial`.
- `data` contains at least one usable value.
- `error_category` and a safe `error_message` are present.
- `retryable` reflects the error, but the runtime still does not retry.

### Failure

- `status` is `failure`.
- `data` is null.
- `error_category` and a safe `error_message` are present.
- `truncated` is false unless an oversized error response was deliberately discarded.

`duration_ms` and `collected_at` are required for every status.

## Raw output and `raw_reference`

v0 does not introduce a raw-artifact store. The bounded `data` retained inside the immutable `ToolResult` is the preserved collector output for the lifetime of the in-memory investigation.

When `data` is present:

- `raw_reference` must equal `tool-result:<ToolResult.id>#/data`;
- the runtime owns creation and resolution of the reference;
- every `EvidenceRecord` derived from the result copies this exact reference; and
- multiple evidence records may use the same reference.

When `data` is null, `raw_reference` is null and no evidence may be produced from the result.

Raw references are investigation-local. They are not file paths, URLs, credentials, or persistent identifiers. Persistence is deferred.

## Output boundary

Each collector must select permitted fields before constructing `ToolResult.data`. It must not store complete Kubernetes objects merely to truncate them later. Each result is limited to 64 KiB after serialization. Lists are deterministically ordered and shortened when necessary, and `truncated` is then true.

Collector-specific allowed fields are defined in the [architecture overview](overview.md#fixed-collectors).
