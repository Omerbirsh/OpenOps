"""Deterministic smoke tests for the installable Phase 1 package."""

import pytest

from openops import __version__
from openops.cli import main

pytestmark = pytest.mark.unit


def test_package_version() -> None:
    assert __version__ == "0.0.0"


def test_placeholder_cli_is_honest(capsys: pytest.CaptureFixture[str]) -> None:
    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "OpenOps is installed, but the investigation runtime is not implemented yet.\n"
    )
