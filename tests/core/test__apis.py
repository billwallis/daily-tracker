"""
Unit tests for the ``daily_tracker.core.apis`` module.
"""

from __future__ import annotations

import abc
import datetime

import pytest

from daily_tracker.core import apis


class SomeInput(apis.Input):
    def __init__(self, value: str):
        self.value = value

    def on_event(self, date_time: datetime.datetime) -> list:
        return ["some-input", "some-other-input"]


class SomeOutput(apis.Output):
    def __init__(self, other_value: str):
        self.other_value = other_value

    def post_event(self, entry) -> None:
        pass


class SomeInputOutput(apis.Input, apis.Output):
    def on_event(self, date_time: datetime.datetime) -> list:
        return ["some-input-with-output", "some-other-input-with-output"]

    def post_event(self, entry) -> None:
        pass


@pytest.fixture(scope="module")
def some_input() -> apis.Input:
    """
    Return a ``Input`` instance.
    """
    return SomeInput("input")


@pytest.fixture(scope="module")
def some_output() -> apis.Output:
    """
    Return an ``Output`` instance.
    """
    return SomeOutput("output")


@pytest.fixture(scope="module")
def some_input_output() -> apis.API:
    """
    Return an ``Input`` and ``Output`` mixin instance.
    """
    return SomeInputOutput()


def test__api():
    """
    Test the ``API`` class.
    """
    assert issubclass(apis.API, abc.ABC)


def test__iinput():
    """
    Test the ``IInput`` class.
    """
    assert issubclass(apis.IInput, abc.ABC)
    assert hasattr(apis.IInput, "on_event")


def test__ioutput():
    """
    Test the ``IOutput`` class.
    """
    assert issubclass(apis.IOutput, abc.ABC)
    assert hasattr(apis.IOutput, "post_event")


def test__input():
    """
    Test the ``Input`` class.
    """
    assert issubclass(apis.Input, apis.API)
    assert issubclass(apis.Input, apis.IInput)
    assert issubclass(apis.Input, abc.ABC)
    assert hasattr(apis.Input, "apis")
    assert hasattr(apis.Input, "on_event")


def test__input__apis(some_input, some_input_output):
    """
    Test the ``Input.apis`` class variable.
    """
    # fmt: off
    assert sorted(apis.Input.apis.keys()) == sorted(["some_input", "some_input_output"])
    # fmt: on
    assert apis.Input.apis["some_input"] == some_input
    assert apis.Input.apis["some_input_output"] == some_input_output
    assert getattr(apis.Input.apis["some_input"], "value") == "input"
    assert not hasattr(apis.Input.apis["some_input_output"], "value")


def test__input__apis__raises(some_output):
    """
    Test that the ``Input.apis`` class variable raises a key error.
    """
    with pytest.raises(KeyError):
        assert apis.Input.apis["some_output"]


def test__input__on_events():
    """
    Test the ``Input.on_events`` method.
    """
    date_time = datetime.datetime(2020, 1, 1)

    actual = sorted(apis.Input.on_events(date_time))  # type: ignore
    expected = sorted(
        [
            "some-input",
            "some-input-with-output",
            "some-other-input",
            "some-other-input-with-output",
        ]
    )

    assert actual == expected


def test__output():
    """
    Test the ``Output`` class.
    """
    assert issubclass(apis.Output, apis.API)
    assert issubclass(apis.Output, apis.IOutput)
    assert issubclass(apis.Output, abc.ABC)
    assert hasattr(apis.Output, "apis")
    assert hasattr(apis.Output, "post_event")


def test__output__apis(some_output, some_input_output):
    """
    Test the ``API`` class.
    """
    # fmt: off
    assert sorted(apis.Output.apis.keys()) == sorted(["some_output", "some_input_output"])
    # fmt: on
    assert apis.Output.apis["some_output"] == some_output
    assert apis.Output.apis["some_input_output"] == some_input_output
    assert getattr(apis.Output.apis["some_output"], "other_value") == "output"
    assert not hasattr(apis.Output.apis["some_input_output"], "other_value")


@pytest.mark.skip("Need to figure out how to test this")
def test__output__post_events():
    """
    Test the ``Output.post_events`` method.

    TODO: Need to figure out how to test this.
        - https://stackoverflow.com/a/69620212/8213085
    """
    entry = "some-entry"
    apis.Output.post_events(entry=entry)  # type: ignore


def test__task():
    """
    Test the ``Task`` class.
    """
    task = apis.Task(task_name="some-task")

    assert task.task_name == "some-task"
    assert task.details == []
    assert task.priority == 1
    assert task.is_default is False


def test__entry():
    """
    Test the ``Entry`` class.
    """
    task = apis.Entry(
        date_time=datetime.datetime(2020, 1, 1),
        task_name="some-task",
        detail="some-detail",
        interval=1,
    )

    assert task.date_time == datetime.datetime(2020, 1, 1)
    assert task.task_name == "some-task"
    assert task.detail == "some-detail"
    assert task.interval == 1
