# ToolResult v0

`ToolResult` is the deterministic envelope returned by every tool execution.

It normalizes complete success, partial success, and failure so the investigation runtime does not need tool-specific error handling.

---

## success

Purpose: Indicates whether the tool completed successfully.

Type: Boolean.

Lifecycle Owner: Set by the tool adapter after execution.

Rules:

- `true` means the requested operation completed successfully.
- `false` means the operation failed or produced only a partial result.

---

## data

Purpose: Stores the normalized result returned by the tool.

Type: Tool-specific structured data or null.

Lifecycle Owner: Written by the tool adapter.

Rules:
- Present when usable data was returned.
- May be present even when `success` is `false` if the tool produced a partial result.
- Must be `null` when no usable data was returned.

---
## raw_reference

Purpose: Points to the preserved raw output produced by this tool execution.

Type: Reference metadata or null.

Examples:

- Stored stdout and stderr artifact path
- Preserved Kubernetes API response location
- Raw command output artifact identifier
- Log output location

Lifecycle Owner: Set by the tool adapter after execution.

Rules:

- Must be present when raw output was produced and preserved.
- May be `null` when the tool produced no output.
- Evidence created from this result must reference this raw output.
- Must not contain normalized investigation conclusions.

---

## error_category

Purpose: Classifies the reason the tool did not complete successfully.

Type: Enumeration or null.

Values:

- invalid_input
- authentication
- authorization
- not_found
- timeout
- unavailable
- rate_limited
- execution_error
- malformed_response
- unknown

Lifecycle Owner: Set by the tool adapter when `success` is `false`.

Rules:

- Must be `null` when the tool completes successfully.
- Must be present when the tool fails.

---

## retryable

Purpose: Indicates whether repeating the same tool call may succeed without changing the request.

Type: Boolean.

Lifecycle Owner: Set by the tool adapter based on the error category and execution result.

Examples:

- A timeout may be retryable.
- An authorization failure is not retryable.
- An invalid workload name is not retryable.

---

## duration_ms

Purpose: Records how long the tool execution took.

Type: Non-negative integer representing milliseconds.

Lifecycle Owner: Measured by the tool runtime.

Rules:

- Includes the complete tool execution duration.
- Must be present for both successful and failed executions.

---

## truncated

Purpose: Indicates whether the returned data or raw output was shortened because of an output limit.

Type: Boolean.

Lifecycle Owner: Set by the tool adapter.

Rules:

- `true` means some output was omitted.
- `false` means the complete available output was returned.
- A truncated result may still be successful and usable.

---

## Result Semantics

A complete success has:

- `success: true`
- usable `data`
- `raw_reference` when raw output was preserved
- `error_category: null`
- `retryable: false`
- a recorded `duration_ms`
- an explicit `truncated` value

A partial result has:

- `success: false`
- some usable `data` or preserved raw output
- an `error_category`
- an explicit `retryable` value
- a recorded `duration_ms`
- an explicit `truncated` value

A complete failure has:

- `success: false`
- `data: null`
- `raw_reference: null` unless error output was preserved
- an `error_category`
- an explicit `retryable` value
- a recorded `duration_ms`
- an explicit `truncated` value