"""
Utilities to use throughout the modules.
"""
import pathlib

ROOT = pathlib.Path(__file__).parent  # resolve to `src/daily_tracker`


def pascal_to_snake(text: str) -> str:
    """
    Convert a pascal-case string to a snake-case string.

    Adapted from:

    - https://stackoverflow.com/a/44969381/8213085

    Note that this splits on *every* uppercase letter, including consecutive
    ones::

        >>> pascal_to_snake(text="HTTP")
        'h_t_t_p'

    :param text: The pascal-case string to convert into a snake-case string. A
     pascal-case string has a capital letter at the start of each word with no
     separator between words, such as "PascalCase".

    :return: The snake-case version of the input string.
    """
    return "".join(
        [
            f"_{letter.lower()}" if letter.isupper() else letter
            for letter in text
        ]
    ).strip("_")


def string_list_to_list(string_list: str, sep: str = ",") -> list:
    """
    Convert a string list to a Python list by splitting on the separator.
    """
    return (
        [category.strip() for category in string_list.split(sep)]
        if string_list
        else []
    )


def get_first_item_in_dict(dictionary: dict) -> tuple:
    """
    Return the first key and value in a dictionary as a tuple.
    """
    return next(iter(dictionary.items()))
