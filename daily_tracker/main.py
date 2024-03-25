"""
Connect the various subpackages throughout the project to couple up the
objects.
"""

import datetime
import logging
import logging.config

import _actions
import yaml

import core
import core.create
import core.database
import core.scheduler
import tracker_utils

APPLICATION_CREATED = True


def create_form(at_datetime: datetime.datetime) -> None:
    """
    Launch the tracker.
    """
    _actions.ActionHandler(at_datetime)


def main(debug_mode: bool = False) -> None:
    """
    Entry point into this project.
    """
    (tracker_utils.ROOT / "logs").mkdir(exist_ok=True)
    with open(tracker_utils.SRC / "logger.yaml") as f:
        logging.config.dictConfig(yaml.safe_load(f.read()))

    logging.info("Starting tracker...")
    logging.debug(f"Setting root directory to {tracker_utils.SRC}")

    if debug_mode:
        create_form(datetime.datetime.now())
        quit()

    if APPLICATION_CREATED:
        scheduler = core.scheduler.IndefiniteScheduler(create_form)
        scheduler.schedule_first()
    else:
        # core.create.create_env()
        db_handler = core.database.DatabaseHandler(
            tracker_utils.SRC / "tracker.db",
            core.Configuration.from_default(),
        )
        # db_handler.import_history(tracker_utils.ROOT / "tracker.csv")
