"""
Unit tests for the ``daily_tracker.tracker_utils`` module.
"""

import daily_tracker.tracker_utils as tracker_utils


def test__pascal_to_snake():
    """
    Test that a pascal-case string is converted to a snake-case string.
    """
    text = "PascalCase"
    expected = "pascal_case"

    assert expected == tracker_utils.pascal_to_snake(text)


def test__string_list_to_list():
    """
    Test that a string of delimited values is split into a list with each
    element trimmed.
    """
    string_ = "-1,0,1,a,bb,ccc,, ,\t"
    expected = ["-1", "0", "1", "a", "bb", "ccc", "", "", ""]

    assert expected == tracker_utils.string_list_to_list(string_)


def test__get_first_item_in_dict():
    """
    Test that the first key and value in a dictionary are returned as a
    tuple.
    """
    dictionary = {"a": 1, "b": 2, "c": 3}
    expected = ("a", 1)

    assert expected == tracker_utils.get_first_item_in_dict(dictionary)
