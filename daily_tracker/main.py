"""
Connect the various subpackages throughout the project to couple up the
objects.
"""

import datetime
import logging
import logging.config

import _actions
import dotenv
import yaml

import core
import core.create
import core.database
import core.scheduler
import utils

dotenv.load_dotenv(dotenv_path=utils.ROOT / ".env")

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
    (utils.ROOT / "logs").mkdir(exist_ok=True)
    with open(utils.SRC / "logger.yaml") as f:
        logging.config.dictConfig(yaml.safe_load(f.read()))

    _in_debug_mode = " in debug mode" if debug_mode else ""
    logging.info(f"Starting tracker{_in_debug_mode}...")
    logging.debug(f"Setting root directory to {utils.ROOT}")
    logging.debug(f"Setting source directory to {utils.SRC}")

    if debug_mode:
        create_form(datetime.datetime.now())
        quit()

    if APPLICATION_CREATED:
        scheduler = core.scheduler.IndefiniteScheduler(create_form)
        scheduler.schedule_first()
    else:
        # core.create.create_env()
        db_handler = core.database.Database(
            utils.SRC / "tracker.db",
            core.Configuration.from_default(),
        )
        # db_handler.import_history(utils.ROOT / "tracker.csv")
