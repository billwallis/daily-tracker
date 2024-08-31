"""
Unit tests for the ``daily_tracker.core.scheduler`` module.
"""

import datetime

import pytest

from daily_tracker.core import scheduler

# Just for brevity
iso = datetime.datetime.fromisoformat


@pytest.mark.parametrize(
    "from_time, interval_in_minutes, expected_next_interval",
    [
        (iso("2020-01-01 00:00:00"), 15, iso("2020-01-01 00:15:00")),
        (iso("2020-01-01 00:01:00"), 15, iso("2020-01-01 00:15:00")),
        (iso("2020-01-01 00:51:00"), 10, iso("2020-01-01 01:00:00")),
        (iso("2020-01-01 23:59:00"), 1, iso("2020-01-02 00:00:00")),
        (iso("2020-01-01 00:10:00"), 3, iso("2020-01-01 00:12:00")),
    ],
)
def test__get_next_interval(
    from_time: datetime.datetime,
    interval_in_minutes: int,
    expected_next_interval: datetime.datetime,
):
    """
    Datetimes are 'rounded up' to the nearest interval.
    """
    assert expected_next_interval == scheduler.get_next_interval(
        from_time=from_time,
        interval_in_minutes=interval_in_minutes,
    )
