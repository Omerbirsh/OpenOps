"""Fail without printing secret values when detect-secrets finds a candidate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

EXCLUDED_FILES = {"BuildingRoadMap.pdf", "uv.lock"}
PUBLIC_IMAGE_DIGEST_LINE = r"nginx:1\.27\.5-alpine@sha256:"


def candidate_files() -> list[str]:
    """Return tracked and untracked, non-ignored files eligible for scanning."""
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Git could not enumerate files for the secret check.")

    files = [path for path in result.stdout.split("\0") if path]
    return sorted(path for path in files if path not in EXCLUDED_FILES and Path(path).is_file())


def scan(files: list[str]) -> dict[str, object]:
    """Run detect-secrets without online verification and return its JSON object."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "detect_secrets",
            "scan",
            "--no-verify",
            "--slim",
            "--exclude-lines",
            PUBLIC_IMAGE_DIGEST_LINE,
            *files,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("detect-secrets could not complete the scan.")

    payload: object = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("detect-secrets returned an unexpected result.")
    return cast(dict[str, object], payload)


def main() -> int:
    """Return nonzero for scanner errors or potential secrets."""
    try:
        files = candidate_files()
        payload = scan(files)
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Secret check failed safely: {error}", file=sys.stderr)
        return 2

    raw_results = payload.get("results")
    if not isinstance(raw_results, dict):
        print("Secret check failed safely: missing results object.", file=sys.stderr)
        return 2

    findings: list[tuple[str, int | str, str]] = []
    for raw_path, raw_entries in raw_results.items():
        if not isinstance(raw_path, str) or not isinstance(raw_entries, list):
            print("Secret check failed safely: malformed finding.", file=sys.stderr)
            return 2
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                print("Secret check failed safely: malformed finding.", file=sys.stderr)
                return 2
            line_number = raw_entry.get("line_number", "unknown")
            secret_type = raw_entry.get("type", "unknown")
            findings.append((raw_path, cast(int | str, line_number), str(secret_type)))

    if findings:
        print("Potential secrets detected; values are redacted:", file=sys.stderr)
        for path, line_number, secret_type in findings:
            print(f"- {path}:{line_number} ({secret_type})", file=sys.stderr)
        return 1

    print(f"Secret check passed for {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
