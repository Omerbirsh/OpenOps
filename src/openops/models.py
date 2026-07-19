"""Typed v0 investigation contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Observation = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
EvidenceId = Annotated[str, StringConstraints(pattern=r"^evidence-[0-9]{3}$")]


class FrozenModel(BaseModel):
    """Strict immutable base for contract values."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceTool(StrEnum):
    DEPLOYMENT = "kubernetes_deployment"
    PODS = "kubernetes_pods"
    EVENTS = "kubernetes_events"


class ToolStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class ErrorCategory(StrEnum):
    INVALID_INPUT = "invalid_input"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    MALFORMED_RESPONSE = "malformed_response"
    EXECUTION_ERROR = "execution_error"


class Sensitivity(StrEnum):
    INTERNAL = "internal"
    SENSITIVE = "sensitive"


class InvestigationPhase(StrEnum):
    COLLECTING = "collecting"
    DECIDING = "deciding"
    FINISHED = "finished"


class InvestigationStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FailureStage(StrEnum):
    COLLECTION = "collection"
    NORMALIZATION = "normalization"
    MODEL = "model"
    VALIDATION = "validation"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InvestigationObjective(FrozenModel):
    cluster_context: str
    namespace: str
    workload_kind: Literal["Deployment"]
    workload_name: str
    symptom: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    time_window_seconds: int = Field(ge=1, le=3600)


class EvidenceTarget(FrozenModel):
    cluster_context: str
    namespace: str
    resource_kind: str
    resource_name: str


class KubernetesCondition(FrozenModel):
    type: str
    status: str
    reason: str | None = None


class ReadinessProbe(FrozenModel):
    type: Literal["http_get"]
    scheme: str
    path: str
    port: int | str
    initial_delay_seconds: int
    period_seconds: int
    timeout_seconds: int
    success_threshold: int
    failure_threshold: int


class DeploymentContainer(FrozenModel):
    name: str
    readiness_probe: ReadinessProbe | None


class DeploymentData(FrozenModel):
    uid: str
    name: str
    namespace: str
    generation: int
    desired_replicas: int
    ready_replicas: int
    available_replicas: int
    unavailable_replicas: int
    observed_generation: int | None
    strategy: str
    selector: dict[str, str]
    containers: tuple[DeploymentContainer, ...]
    conditions: tuple[KubernetesCondition, ...]


class PodContainer(FrozenModel):
    name: str
    ready: bool
    restart_count: int
    state: Literal["waiting", "running", "terminated", "unknown"]


class PodData(FrozenModel):
    uid: str
    name: str
    namespace: str
    owner_uids: tuple[str, ...]
    phase: str
    conditions: tuple[KubernetesCondition, ...]
    containers: tuple[PodContainer, ...]


class PodsData(FrozenModel):
    pods: tuple[PodData, ...]


class InvolvedObject(FrozenModel):
    uid: str
    kind: str
    namespace: str
    name: str


class EventData(FrozenModel):
    uid: str
    type: str
    reason: str
    message: Annotated[str, StringConstraints(max_length=512)]
    count: int
    first_seen: datetime | None
    last_seen: datetime | None
    involved_object: InvolvedObject


class EventsData(FrozenModel):
    events: tuple[EventData, ...]


ToolData = DeploymentData | PodsData | EventsData


class ToolResult(FrozenModel):
    id: Annotated[str, StringConstraints(pattern=r"^tool-[0-9]{3}$")]
    source_tool: SourceTool
    collected_at: datetime
    status: ToolStatus
    data: ToolData | None
    raw_reference: str | None
    error_category: ErrorCategory | None
    error_message: Annotated[str, StringConstraints(max_length=512)] | None
    retryable: bool
    duration_ms: int = Field(ge=0)
    truncated: bool

    @model_validator(mode="after")
    def validate_status_invariants(self) -> ToolResult:
        expected_reference = f"tool-result:{self.id}#/data"
        if self.data is None and self.raw_reference is not None:
            raise ValueError("a result without data cannot have a raw reference")
        if self.data is not None and self.raw_reference != expected_reference:
            raise ValueError("a result with data must use its investigation-local raw reference")
        expected_data_type = {
            SourceTool.DEPLOYMENT: DeploymentData,
            SourceTool.PODS: PodsData,
            SourceTool.EVENTS: EventsData,
        }[self.source_tool]
        if self.data is not None and not isinstance(self.data, expected_data_type):
            raise ValueError("collector data does not match its source tool")
        if self.status is ToolStatus.SUCCESS:
            if (
                self.data is None
                or self.error_category is not None
                or self.error_message is not None
            ):
                raise ValueError("a successful result must contain only usable data")
            if self.retryable:
                raise ValueError("a successful result cannot be retryable")
        elif self.status is ToolStatus.PARTIAL:
            if self.data is None or self.error_category is None or self.error_message is None:
                raise ValueError("a partial result requires data and a safe error")
        elif self.data is not None or self.error_category is None or self.error_message is None:
            raise ValueError("a failed result requires a safe error and no data")
        return self


class EvidenceRecord(FrozenModel):
    id: EvidenceId
    source_tool: SourceTool
    timestamp: datetime
    target: EvidenceTarget
    observation: Observation
    sensitivity: Sensitivity
    raw_reference: str


class FinalDiagnosis(FrozenModel):
    cause: LongText
    confidence: Confidence
    evidence_ids: tuple[EvidenceId, ...] = Field(min_length=1)
    alternatives: tuple[ShortText, ...] = Field(max_length=5)
    recommendation: LongText


class InvestigationLimits(FrozenModel):
    max_tool_executions: Literal[3] = 3
    max_tool_result_bytes: Literal[65536] = 65536
    max_event_items: Literal[20] = 20
    max_evidence_records: Literal[20] = 20
    max_model_calls: Literal[1] = 1
    max_model_output_tokens: Literal[1000] = 1000


class FailureSummary(FrozenModel):
    stage: FailureStage
    category: ErrorCategory
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]


class InvestigationState(BaseModel):
    """Runtime-owned mutable envelope with immutable appended records."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    objective: InvestigationObjective
    phase: InvestigationPhase = InvestigationPhase.COLLECTING
    status: InvestigationStatus = InvestigationStatus.RUNNING
    tool_results: list[ToolResult] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    decision: FinalDiagnosis | None = None
    limits: InvestigationLimits = Field(default_factory=InvestigationLimits)
    failure: FailureSummary | None = None


class InvestigationOutcome(FrozenModel):
    state: InvestigationState
    report: str | None
