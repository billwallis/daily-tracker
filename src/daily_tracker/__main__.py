"""
Connect the various subpackages throughout the project to couple up the objects.
"""
import datetime
import logging
import logging.config

import yaml

import daily_tracker.core.configuration
import daily_tracker.core.database
import daily_tracker.core.form
import daily_tracker.core.scheduler
import daily_tracker.create
import daily_tracker.utils

APPLICATION_CREATED = True


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
        scheduler = daily_tracker.core.scheduler.IndefiniteScheduler(
            create_form
        )
        scheduler.schedule_first()
    else:
        # daily_tracker.create.create_env()
        db_handler = daily_tracker.core.database.DatabaseHandler(
            daily_tracker.utils.ROOT / "tracker.db",
            daily_tracker.core.configuration.get_configuration(),
        )
        # db_handler.import_history(daily_tracker.utils.ROOT / "tracker.csv")


if __name__ == "__main__":
    main()
