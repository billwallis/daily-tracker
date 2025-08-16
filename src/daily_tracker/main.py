"""
Connect the various subpackages throughout the project to couple up the
objects.
"""

import datetime
import logging
import logging.config

import dotenv
import yaml
from wakepy import keep

from daily_tracker import _actions, core, utils
from daily_tracker.core import database, scheduler

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
    with open(utils.DAILY_TRACKER / "logger.yaml") as f:
        logging.config.dictConfig(yaml.safe_load(f.read()))

    _in_debug_mode = " in debug mode" if debug_mode else ""
    logging.info(f"Starting tracker{_in_debug_mode}...")
    logging.debug(f"Setting root directory to {utils.ROOT}")
    logging.debug(f"Setting source directory to {utils.DAILY_TRACKER}")

    if not APPLICATION_CREATED:
        # create.create_env()
        db_handler = database.Database(  # noqa: F841
            utils.DAILY_TRACKER / "tracker.db",
            core.Configuration.from_default(),
        )
        # db_handler.import_history(utils.ROOT / "tracker.csv")

    if debug_mode:
        create_form(datetime.datetime.now())
        return

    config = core.Configuration.from_default()
    indefinite_scheduler = scheduler.IndefiniteScheduler(create_form)

    if config.keep_awake:
        with keep.presenting():
            indefinite_scheduler.schedule_first()
    else:
        indefinite_scheduler.schedule_first()

    logging.info("Closing tracker...")


if __name__ == "__main__":
    main(debug_mode=False)
