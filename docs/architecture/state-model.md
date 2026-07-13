# InvestigationState v0

`InvestigationState` is the structured record of one OpenOps investigation.

It is created when an investigation starts and updated as the runtime collects evidence and produces a diagnosis.

## objective

Purpose: Defines what OpenOps is investigating.

Type: Investigation objective containing:

* cluster_context: string
* namespace: string
* workload_kind: string
* workload_name: string
* symptom: string
* time_window: optional string

Lifecycle owner: Intake.

Created once and not modified after the investigation starts.

## phase

Purpose: Identifies the current investigation step.

Type: Enum:

* intake
* collecting_evidence
* deciding
* finished

Lifecycle owner: Investigation runtime.

Updated when the investigation moves between steps.

## tool_results

Purpose: Stores the execution results returned by tools during the investigation.

Type: List of `ToolResult` objects as defined in `tool-contract.md`.

Lifecycle Owner: Investigation runtime.

Rules:

- One record is appended for every tool execution.
- Results are stored before evidence normalization occurs.
- Results are not modified after being recorded.
- A failed or partial tool execution must still be recorded.

## evidence

Purpose: Stores normalized factual observations collected during the investigation.

Type: List of `EvidenceRecord` objects as defined in `evidence-model.md`.

Lifecycle Owner: Evidence normalization stage.

Rules:

- Records are appended after tool results are normalized into evidence.
- Records are not modified after creation.
- Each record must reference the raw tool output from which it was derived.
- The diagnosis may cite evidence only through evidence IDs.

## decision

Purpose: Stores the final diagnosis.

Type: Optional diagnosis containing:

* cause: string
* confidence: string
* evidence_ids: list of strings
* alternatives: list of strings
* recommendation: string

Lifecycle owner: Decision stage.

Empty until enough evidence has been collected, then written once.

## budgets

Purpose: Prevents the investigation from running without limits.

Type: Execution limits containing:

* max_evidence_items: integer
* max_steps: integer

Lifecycle owner: Investigation runtime.

Defined when the investigation starts and read during execution.

## status

Purpose: Represents the final operational state of the investigation.

Type: Enum:

* running
* completed
* failed

Lifecycle owner: Investigation runtime.

Starts as `running` and ends as either `completed` or `failed`.
