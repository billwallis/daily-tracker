from __future__ import annotations

import argparse
import importlib.metadata
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
    daily_tracker.report(getattr(args, "report-name"))
    return SUCCESS


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

    parser__foo = subparsers.add_parser(
        "run",
        help="Start the tracker and schedule the pop-up boxes.",
    )
    parser__foo.add_argument(
        "--debug",
        action="store_true",
        help="Run the tracker in debug mode.",
    )

    parser__bar = subparsers.add_parser(
        "report",
        help="Print a report of recent entries.",
    )
    parser__bar.add_argument(
        "report-name",
        help="Name of the report to run.",
    )

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    if args.command == "report":
        return _report(args)

    parser.print_help()
    return SUCCESS
