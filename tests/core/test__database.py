"""
Unit tests for the ``daily_tracker.core.database`` module.
"""

import pytest

from daily_tracker import utils
from daily_tracker.core import configuration, database


@pytest.mark.skip(reason="Should use a fake database")
def test__get_recent_tasks():
    """
    The most recent tasks are returned.
    """
    database_handler = database.Database(
        database_filepath=utils.DB,
        configuration=configuration.Configuration.from_default(),
    )

    print(database_handler.get_recent_tasks(show_last_n_weeks=2))
