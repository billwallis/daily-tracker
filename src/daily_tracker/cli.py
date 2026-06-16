from __future__ import annotations

import argparse
import importlib.metadata
import json
from collections.abc import Sequence

import daily_tracker

SUCCESS = 0
FAILURE = 1


def _get_version() -> str:
    return f"(alpha) %(prog)s {importlib.metadata.version('daily-tracker')}"


def _run(args: argparse.Namespace) -> int:
    try:
        daily_tracker.run(debug_mode=args.debug)
    except KeyboardInterrupt:
        return SUCCESS

    return SUCCESS


def _report(args: argparse.Namespace) -> int:
    params = args.params or "{}"
    daily_tracker.report(
        report_name=getattr(args, "report-name"),
        params=json.loads(params),
    )
    return SUCCESS


def _debug() -> int:
    result = SUCCESS
    for rc, status in daily_tracker.debug():
        result |= rc
        print(status)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """
    Parse the arguments and run the command.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=_get_version(),
    )
    subparsers = parser.add_subparsers(dest="command")

    parser__run = subparsers.add_parser(
        "run",
        help="Start the tracker and schedule the pop-up boxes.",
    )
    parser__run.add_argument(
        "--debug",
        action="store_true",
        help="Run the tracker in debug mode.",
    )

    parser__report = subparsers.add_parser(
        "report",
        help="Print a report of recent entries.",
    )
    parser__report.add_argument(
        "report-name",
        help="Name of the report to run.",
    )
    parser__report.add_argument(
        "--params",
        help="JSON value of parameters to pass to the report query.",
    )

    subparsers.add_parser("debug")

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    if args.command == "report":
        return _report(args)
    if args.command == "debug":
        return _debug()

    parser.print_help()
    return SUCCESS
