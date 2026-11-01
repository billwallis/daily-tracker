from __future__ import annotations

import argparse
import importlib.metadata
from collections.abc import Sequence
from typing import Any

import daily_tracker

SUCCESS = 0
FAILURE = 1

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
CYAN = "\033[1;36m"
GREY = "\033[38;5;240m"
BOLD = "\033[1m"
RESET = "\033[0m"


def colour(text: str, colour_: str) -> str:
    return f"{colour_}{text}{RESET}"


def _get_version() -> str:
    return f"(alpha) %(prog)s {importlib.metadata.version('daily-tracker')}"


def _run(args: argparse.Namespace) -> int:
    try:
        daily_tracker.run(debug_mode=args.debug)
    except KeyboardInterrupt:
        return SUCCESS

    return SUCCESS


def _parse_values(key: str, values: list) -> tuple[str, Any]:
    if len(values) == 0:
        if key.startswith("no-"):
            return key[3:], False
        else:
            return key, True
    elif len(values) == 1:
        return key, values[0]
    else:
        return key, values


def _collect_unknown_args(args: Sequence[str]) -> dict[str, str]:
    if not args:
        return {}
    if not args[0].startswith("--"):
        raise ValueError(
            "could not parse unknown args: first argument must be a flag, not a value"
        )

    key, values = None, []
    result = dict()
    for item in args:
        if item == "--":
            raise ValueError("'--' is unsupported")
        elif item.startswith("--"):
            if key is not None:
                assert isinstance(key, str)
                k, v = _parse_values(key, values)
                result[k] = v

            key = item[2:]
            values = []
        else:
            assert key is not None
            values.append(item)

    assert key is not None
    k, v = _parse_values(key, values)
    result[k] = v

    return result


def _report(args: argparse.Namespace, unknown_args: Sequence[str]) -> int:
    if args.list:
        out = ""
        for r in daily_tracker.get_reports():
            if r.params:
                params = colour(f"(params: {', '.join(r.params)})", GREY)
                out += f"{r.path.stem}  {params}"
            else:
                out += f"{r.path.stem}"
            out += "\n"
        print(out.rstrip("\n"))
        return SUCCESS

    try:
        daily_tracker.report(
            report_name=getattr(args, "report-name"),
            params=_collect_unknown_args(unknown_args),
        )
        return SUCCESS
    except KeyError as err:
        missing_key = str(err)[1:-1]  # trim surrounding quotation marks
        print(
            f"daily-tracker report: error: the following arguments are required: --{missing_key}"
        )
        return FAILURE


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
        nargs="?",
        help="Name of the report to run.",
    )
    parser__report.add_argument(
        "--list",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="List the available reports that can be run.",
    )

    subparsers.add_parser("debug")

    args, unknown_args = parser.parse_known_args(argv)
    if args.command == "run":
        return _run(args)
    if args.command == "report":
        return _report(args, unknown_args)
    if args.command == "debug":
        return _debug()

    parser.print_help()
    return SUCCESS
