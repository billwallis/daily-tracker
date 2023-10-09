"""
Unit tests for the ``daily_tracker.tracker_utils`` module.
"""
import daily_tracker.tracker_utils as tracker_utils


def test__string_list_to_list():
    """
    A string of delimited values is split into a list with each element
    trimmed.
    """
    string_ = "-1,0,1,a,bb,ccc,, ,\t"
    expected = ["-1", "0", "1", "a", "bb", "ccc", "", "", ""]

    assert expected == tracker_utils.string_list_to_list(string_)
