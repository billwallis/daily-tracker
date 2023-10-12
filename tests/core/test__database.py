"""
Unit tests for the ``daily_tracker.core.database`` module.
"""
import pytest

import daily_tracker.core.configuration as configuration
import daily_tracker.core.database as database
import daily_tracker.tracker_utils as tracker_utils


@pytest.mark.skip(reason="Should use a fake database.")
def test__get_recent_tasks():
    """
    The most recent tasks are returned.
    """
    database_handler = database.DatabaseHandler(
        database_filepath=tracker_utils.ROOT / "tracker.db",
        configuration=configuration.Configuration.from_default(),
    )

    print(database_handler.get_recent_tasks(show_last_n_weeks=2))
