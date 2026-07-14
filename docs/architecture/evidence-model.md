# EvidenceRecord v0

An `EvidenceRecord` is one immutable factual observation produced by deterministic normalization of a stored `ToolResult`.

Evidence is the only collected Kubernetes information available to the decision model. A record describes what was observed; it does not state a cause or recommendation.

## Fields

| Field | Type | Owner and rule |
| --- | --- | --- |
| `id` | string | Normalizer-assigned, unique within the investigation. IDs use stable sequence form `evidence-001`, `evidence-002`, and so on after canonical sorting. |
| `source_tool` | enum | Copied from the source `ToolResult`: `kubernetes_deployment`, `kubernetes_pods`, or `kubernetes_events`. |
| `timestamp` | timestamp | Copied from the source `ToolResult.collected_at`; it is collection time, not event occurrence time. |
| `target` | object | `cluster_context`, `namespace`, `resource_kind`, and `resource_name`. |
| `observation` | string, 1-512 characters | A fact generated from a fixed normalizer template. |
| `sensitivity` | enum | `internal` or `sensitive`. All model-visible v0 records must be `internal`; a potential secret is not emitted as evidence. |
| `raw_reference` | string | Exact copy of the source `ToolResult.raw_reference`. |

The normalizer owns all fields. Records are appended to `InvestigationState.evidence` and never modified.

## Provenance invariants

- `raw_reference` must resolve to one `ToolResult.data` value in the same `InvestigationState`.
- `source_tool` and `timestamp` must match that `ToolResult`.
- A failed `ToolResult` with no data produces no evidence.
- A successful or partial result may produce zero or more records.
- Multiple records may reference the same result data.
- The report and diagnosis cite evidence by `EvidenceRecord.id`, never by `ToolResult.id` or `raw_reference`.

## Deterministic normalization

Normalization is application code, not a model call. For identical objective and fixture input, it must produce the same ordered observations and IDs.

The normalizer:

1. processes results in fixed collector order;
2. processes Pods by resource name;
3. processes Events in stored collector order: `last_seen` descending, involved-object UID, reason, and Event UID;
4. reads only the allowlisted fields documented for each collector;
5. generates observations from controlled templates rather than copying arbitrary object text; and
6. stops with an investigation failure if more than 20 evidence records would be produced.

Examples of valid observations are:

- `Deployment readiness-demo has 1 desired replica and 0 available replicas.`
- `Container web has an HTTP readiness probe configured for path /ready on port 80.`
- `Pod readiness-demo-abc is Running and its Ready condition is False.`
- `Container web is not ready and has restarted 0 times.`
- `Kubernetes reported an Unhealthy readiness probe result with HTTP status 404 for Pod readiness-demo-abc.`

The following are diagnoses and must not be emitted as evidence:

- `The readiness probe is misconfigured.`
- `The application should change its health endpoint.`

## Untrusted text

Labels, annotations, managed fields, environment variables, volume content, and complete Event messages are never copied into evidence. For the reference scenario, the Event normalizer may extract only the involved target, Event type and reason, occurrence metadata, the fact that the failure concerns readiness, and a recognized HTTP status code. Unknown Event message text remains in bounded `ToolResult.data` and is not sent to the model.
