"""
Utilities to use throughout the modules.
"""
import pathlib


ROOT = pathlib.Path(__file__).parent  # resolve to `src/daily_tracker`


def string_list_to_list(string_list: str, sep: str = ",") -> list:
    """
    Convert a string list to a Python list by splitting on the separator.
    """
    return [category.strip() for category in string_list.split(sep)] if string_list else []


def get_first_item_in_dict(dictionary: dict) -> tuple:
    """
    Return the first key and value in a dictionary as a tuple.
    """
    return next(iter(dictionary.items()))
