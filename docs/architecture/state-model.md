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

## evidence

Purpose: Stores observations collected from Kubernetes.

Type: List of evidence records.

Each evidence record contains:

* id: string
* source: string
* observation: string

Lifecycle owner: Evidence collector.

Records are appended during evidence collection and are not modified afterward.

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
