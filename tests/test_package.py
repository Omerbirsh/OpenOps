"""Deterministic smoke tests for the installable Phase 1 package."""

import pytest

from openops import __version__

pytestmark = pytest.mark.unit


def test_package_version() -> None:
    assert __version__ == "0.0.1"
