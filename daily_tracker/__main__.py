"""
Entry point into the application.
"""

import argparse

from daily_tracker import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="daily-tracker",
        description="An application for keeping track of tasks throughout the day.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the application in debug mode.",
    )
    args = parser.parse_args()

    main.main(debug_mode=args.debug)
