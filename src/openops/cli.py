"""Truthful Phase 1 console entry point."""

import sys


def main() -> int:
    """Report that investigation behavior has not been implemented."""
    print(
        "OpenOps is installed, but the investigation runtime is not implemented yet.",
        file=sys.stderr,
    )
    return 2
