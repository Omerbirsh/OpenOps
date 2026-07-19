"""Fixed v0 CLI intake validation."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import ValidationError

from openops.models import InvestigationObjective

EXPECTED_CONTEXT = "openops-reader@kind-openops-lab"
EXPECTED_NAMESPACE = "openops-lab"
EXPECTED_KIND: Literal["Deployment"] = "Deployment"
EXPECTED_WORKLOAD = "readiness-demo"
DEFAULT_TIME_WINDOW = "30m"
_DURATION_PATTERN = re.compile(r"^(?P<amount>[1-9][0-9]*)(?P<unit>[smh])$")


class IntakeError(ValueError):
    """A safe error raised before any external client is constructed."""


def parse_duration(value: str) -> int:
    match = _DURATION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise IntakeError("time window must use a positive duration such as 30m")
    amount = int(match.group("amount"))
    multiplier = {"s": 1, "m": 60, "h": 3600}[match.group("unit")]
    seconds = amount * multiplier
    if seconds > 3600:
        raise IntakeError("time window must not exceed 60m")
    return seconds


def validate_intake(
    *,
    cluster_context: str,
    namespace: str,
    workload_kind: str,
    workload_name: str,
    symptom: str,
    time_window: str = DEFAULT_TIME_WINDOW,
) -> InvestigationObjective:
    expected = {
        "cluster context": (cluster_context, EXPECTED_CONTEXT),
        "namespace": (namespace, EXPECTED_NAMESPACE),
        "workload kind": (workload_kind, EXPECTED_KIND),
        "workload name": (workload_name, EXPECTED_WORKLOAD),
    }
    for label, (actual, required) in expected.items():
        if actual != required:
            raise IntakeError(f"{label} must equal {required!r} for v0")
    try:
        return InvestigationObjective(
            cluster_context=cluster_context,
            namespace=namespace,
            workload_kind=EXPECTED_KIND,
            workload_name=workload_name,
            symptom=symptom,
            time_window_seconds=parse_duration(time_window),
        )
    except ValidationError as error:
        raise IntakeError("symptom must contain between 1 and 500 characters") from error
