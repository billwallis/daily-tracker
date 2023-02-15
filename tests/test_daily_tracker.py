import datetime

import pytest

import daily_tracker
import daily_tracker.utils
import daily_tracker.core.scheduler


def test__utils__string_list_to_list():
    """
    A string of delimited values is split into a list with each element trimmed.
    """
    string_ = "-1,0,1,a,bb,ccc,, ,\t"
    expected = ["-1", "0", "1", "a", "bb", "ccc", "", "", ""]

    assert expected == daily_tracker.utils.string_list_to_list(string_)


@pytest.mark.parametrize(
    "from_time, interval_in_minutes, expected_next_interval",
    [
        (datetime.datetime.fromisoformat("2020-01-01 00:00:00"), 15, datetime.datetime.fromisoformat("2020-01-01 00:15:00")),
        (datetime.datetime.fromisoformat("2020-01-01 00:01:00"), 15, datetime.datetime.fromisoformat("2020-01-01 00:15:00")),
        (datetime.datetime.fromisoformat("2020-01-01 00:51:00"), 10, datetime.datetime.fromisoformat("2020-01-01 01:00:00")),
        (datetime.datetime.fromisoformat("2020-01-01 23:59:00"), 1, datetime.datetime.fromisoformat("2020-01-02 00:00:00")),
        (datetime.datetime.fromisoformat("2020-01-01 00:10:00"), 3, datetime.datetime.fromisoformat("2020-01-01 00:12:00")),
    ]
)
def test__core__scheduler__get_next_interval(
    from_time: datetime.datetime,
    interval_in_minutes: int,
    expected_next_interval: datetime.datetime,
):
    """
    Datetimes are 'rounded up' to the nearest interval.
    """
    assert expected_next_interval == daily_tracker.core.scheduler.get_next_interval(
        from_time=from_time,
        interval_in_minutes=interval_in_minutes,
    )
