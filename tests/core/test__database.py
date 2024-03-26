"""
Unit tests for the ``daily_tracker.core.database`` module.
"""

import pytest

import daily_tracker.core.configuration as configuration
import daily_tracker.core.database as database
import daily_tracker.utils as utils


@pytest.mark.skip(reason="Should use a fake database.")
def test__get_recent_tasks():
    """
    The most recent tasks are returned.
    """
    database_handler = database.Database(
        database_filepath=utils.DB,
        configuration=configuration.Configuration.from_default(),
    )

    print(database_handler.get_recent_tasks(show_last_n_weeks=2))
