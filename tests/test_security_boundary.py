"""Structural regression checks for the fixed read-only runtime boundary."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "openops"


def test_runtime_has_no_shell_or_process_execution_path() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in SOURCE_ROOT.glob("*.py"))
    assert "import subprocess" not in source
    assert "os.system" not in source
    assert "kubectl" not in source.lower()


def test_kubernetes_adapter_has_no_write_exec_log_or_generic_api_method() -> None:
    source = (SOURCE_ROOT / "kubernetes_adapter.py").read_text(encoding="utf-8")
    forbidden = (
        ".create_",
        ".patch_",
        ".replace_",
        ".delete_",
        "read_namespaced_pod_log",
        "connect_get_namespaced_pod_exec",
        "call_api(",
    )
    assert all(token not in source for token in forbidden)
