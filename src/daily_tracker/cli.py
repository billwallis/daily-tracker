from __future__ import annotations

import argparse
import pathlib
import tomllib
from collections.abc import Sequence

import daily_tracker.main

SUCCESS = 0
FAILURE = 1
HERE = pathlib.Path(__file__).parent
PYPROJECT = HERE.parent.parent / "pyproject.toml"


def _get_version() -> str:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    return f"alpha {version}"


def _run(args: argparse.Namespace) -> int:
    try:
        daily_tracker.main.main(debug_mode=args.debug)
    except KeyboardInterrupt:
        return SUCCESS

    return SUCCESS


def _report(args: argparse.Namespace) -> int:
    raise NotImplementedError("Not implemented")


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

    parser__foo = subparsers.add_parser("run")
    parser__foo.add_argument("--debug", action="store_true")

    parser__bar = subparsers.add_parser("report")  # noqa: F841

    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args)
    if args.command == "report":
        return _report(args)

    parser.print_help()
    return SUCCESS
