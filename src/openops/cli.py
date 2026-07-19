"""Synchronous command-line entry point for the fixed v0 investigation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from openops.decision import DecisionProvider, OpenAIDecisionProvider
from openops.intake import DEFAULT_TIME_WINDOW, IntakeError, validate_intake
from openops.kubernetes_adapter import (
    KubernetesConfigurationError,
    build_live_collector_suite,
)
from openops.models import (
    ErrorCategory,
    FailureStage,
    InvestigationOutcome,
    InvestigationStatus,
)
from openops.runtime import CollectorSuite, run_investigation
from openops.trace import write_sanitized_trace


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise IntakeError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="openops", description="Evidence-driven Kubernetes investigation")
    subcommands = parser.add_subparsers(dest="command", required=True)
    investigate = subcommands.add_parser(
        "investigate", help="run the fixed broken-readiness investigation"
    )
    investigate.add_argument("--cluster-context", required=True)
    investigate.add_argument("--namespace", required=True)
    investigate.add_argument("--workload-kind", required=True)
    investigate.add_argument("--workload-name", required=True)
    investigate.add_argument("--symptom", required=True)
    investigate.add_argument("--time-window", default=DEFAULT_TIME_WINDOW)
    investigate.add_argument(
        "--trace-file",
        type=Path,
        help="create a sanitized JSON trace without raw Kubernetes data",
    )
    return parser


def _exit_code(outcome: InvestigationOutcome) -> int:
    failure = outcome.state.failure
    if failure is None:
        return 4
    if failure.stage is FailureStage.MODEL:
        return 5
    if failure.stage is FailureStage.VALIDATION:
        return 6
    if any(
        result.error_category in {ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION}
        for result in outcome.state.tool_results
    ):
        return 3
    return 4


def main(
    argv: Sequence[str] | None = None,
    *,
    collectors: CollectorSuite | None = None,
    provider: DecisionProvider | None = None,
) -> int:
    try:
        arguments = _parser().parse_args(argv)
        objective = validate_intake(
            cluster_context=arguments.cluster_context,
            namespace=arguments.namespace,
            workload_kind=arguments.workload_kind,
            workload_name=arguments.workload_name,
            symptom=arguments.symptom,
            time_window=arguments.time_window,
        )
    except IntakeError as error:
        print(f"OpenOps input error: {error}", file=sys.stderr)
        return 2

    try:
        active_collectors = collectors or build_live_collector_suite(objective)
    except KubernetesConfigurationError as error:
        print(f"OpenOps configuration error: {error}", file=sys.stderr)
        return 2
    active_provider = provider or OpenAIDecisionProvider()
    outcome = run_investigation(objective, active_collectors, active_provider)

    if arguments.trace_file is not None:
        try:
            write_sanitized_trace(outcome.state, arguments.trace_file)
        except OSError:
            print(
                "OpenOps trace error: the trace path must be new, writable, and have an existing parent.",
                file=sys.stderr,
            )
            return 2

    if outcome.state.status is InvestigationStatus.COMPLETED and outcome.report is not None:
        print(outcome.report, end="")
        return 0
    failure = outcome.state.failure
    if failure is None:
        print("OpenOps failed without a safe failure summary.", file=sys.stderr)
    else:
        print(f"OpenOps failed during {failure.stage.value}: {failure.message}", file=sys.stderr)
    return _exit_code(outcome)
