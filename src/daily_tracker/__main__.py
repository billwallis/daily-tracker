"""
Connect the various subpackages throughout the project to couple up the objects.
"""
import datetime
import logging
import logging.config
import pathlib

import yaml

import daily_tracker.core.form
import daily_tracker.core.handlers
import daily_tracker.core.scheduler
import daily_tracker.utils

APPLICATION_CREATED = True


def create_env() -> None:
    """
    Create the .env file.
    """
    filepath = ".env"
    if pathlib.Path(filepath).exists():
        return None

    with open(filepath, "w+") as f:
        keys = ["JIRA_URL", "JIRA_KEY", "JIRA_SECRET", "SLACK_URL"]
        f.write("\n".join([f"{key}=" for key in keys]))


def create_form(at_datetime: datetime.datetime) -> None:
    """
    Launch the tracker.
    """
    daily_tracker.core.form.TrackerForm(at_datetime)


def main() -> None:
    """
    Entry point into this project.
    """
    with open(daily_tracker.utils.ROOT / "logger.yaml") as f:
        logging.config.dictConfig(yaml.safe_load(f.read()))

    logging.info("Starting tracker...")
    logging.debug(f"Setting root directory to {daily_tracker.utils.ROOT}")

    if APPLICATION_CREATED:
        scheduler = daily_tracker.core.scheduler.IndefiniteScheduler(create_form)
        scheduler.schedule_first()
    else:
        # create_env()
        db_handler = daily_tracker.core.handlers.DatabaseHandler(daily_tracker.utils.ROOT / "tracker.db")
        # db_handler.import_history(daily_tracker.utils.ROOT / "tracker.csv")


if __name__ == "__main__":
    main()
