"""Tests for contract invariants."""

import pytest
from pydantic import ValidationError

from openops.models import ToolResult
from tests.helpers import fixture_result

pytestmark = pytest.mark.unit


def test_fixture_results_satisfy_contracts() -> None:
    assert fixture_result("deployment").id == "tool-001"
    assert fixture_result("pods").id == "tool-002"
    assert fixture_result("events").id == "tool-003"


def test_success_requires_data_and_exact_raw_reference() -> None:
    payload = fixture_result("deployment").model_dump()
    payload["raw_reference"] = "file:///raw.json"
    with pytest.raises(ValidationError):
        ToolResult.model_validate(payload)


def test_failure_cannot_retain_collector_data() -> None:
    payload = fixture_result("deployment").model_dump()
    payload.update(
        status="failure",
        error_category="execution_error",
        error_message="safe",
    )
    with pytest.raises(ValidationError):
        ToolResult.model_validate(payload)
