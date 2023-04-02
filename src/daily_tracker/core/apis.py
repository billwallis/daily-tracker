# sourcery skip: upper-camel-case-classes,snake-case-variable-declarations
"""
The API classes that all integration classes should inherit from.

This categorises all objects as ``Input`` and ``Output`` objects:

- The ``Input`` objects have an ``on_event`` method which is called before the
  task input is requested from the user.
- The ``Output`` objects have a ``post_event`` method which is called after the
  task input has been received from the user.

The class hierarchy here is::

                +-------+
        +-------|  ABC  |--------+
        |       +-------+        |
        |           |            |
    +--------+  +-------+  +---------+
    | IInput |  |  API  |  | IOutput |
    +--------+  +-------+  +---------+
        |           |            |
        | +-------+ | +--------+ |
        +-| Input |-+-| Output |-+
          +-------+   +--------+

The backend will then only interact with the ``Input`` and ``Output`` type
classes through the corresponding ``APIS`` class property::

    >>> type(Input.APIS), type(Output.APIS)
    (<class 'dict'>, <class 'dict'>)


.. mermaid::

    classDiagram

    ABC --> IInput
    ABC --> API
    ABC --> IOutput

    IInput : on_event()
    API : APIS
    IOutput : post_event()

    IInput --> Input
    IInput --> Output

    API --> Input
    API --> Output

    IOutput --> Input
    IOutput --> Output

    Input : APIS
    Input : on_event()

    Output : APIS
    Output : post_event()
"""
from __future__ import annotations

import abc
import datetime
import logging
from collections.abc import Generator
from typing import ClassVar

import daily_tracker.utils
from daily_tracker.core.data import Entry, Task


class API(abc.ABC):
    """
    Implementation to automatically bind the integration objects to the
    ``Input`` and ``Output`` objects' ``APIS`` class property.
    """

    APIS: ClassVar

    def __init_subclass__(cls, **kwargs) -> None:
        """
        During the initialisation of the subclass, use some metaprogramming to
        automatically bind the subclass to the ``Input`` and ``Output`` classes
        ``APIS`` property.
        """
        if cls.__name__ not in ["Input", "Output"]:
            key = daily_tracker.utils.pascal_to_snake(cls.__name__)
            logging.debug(f"Adding class {cls} to {cls}.APIS with key '{key}'")
            cls.APIS[key] = cls

        return super().__init_subclass__(**kwargs)


class IInput(abc.ABC):
    """
    Abstract base class for objects whose methods need to be actioned when the
    "pop-up" event starts.
    """

    @abc.abstractmethod
    def on_event(self, date_time: datetime.datetime) -> list[Task]:
        """
        The actions to perform at the start of the "pop-up" event at the
        scheduled time.
        """
        pass


class Input(API, IInput):
    """
    Abstract base class for objects whose methods need to be actioned when the
    "pop-up" event starts.
    """

    APIS: ClassVar[dict[str, Input]] = {}

    def on_event(self, date_time: datetime.datetime) -> list[Task]:
        """
        The actions to perform at the start of the "pop-up" event at the
        scheduled time.
        """
        raise NotImplementedError(
            f"{self}.{self.on_event.__name__} has not been defined"
        )


class IOutput(abc.ABC):
    """
    Abstract base class for objects whose methods need to be resolved after the
    "pop-up" event ends.
    """

    @abc.abstractmethod
    def post_event(self, entry: Entry) -> None:
        """
        The actions to perform after the "pop-up" event.
        """
        pass


class Output(API, IOutput):
    """
    Abstract base class for objects whose methods need to be resolved after the
    "pop-up" event ends.
    """

    APIS: ClassVar[dict[str, Output]] = {}

    def post_event(self, entry: Entry) -> None:
        """
        The actions to perform after the "pop-up" event.
        """
        raise NotImplementedError(
            f"{self}.{self.post_event.__name__} has not been defined"
        )


def on_event(date_time: datetime.datetime) -> Generator[list[Task], None, None]:
    """
    Execute the actions at the start of the "pop-up" event.

    For the "pop-up" event, we need:

    1.  The default task and detail to show first
    2.  A list of alternative tasks that are available in the drop-down
    3.  A list of the latest details for each of the tasks from 2

    The UI call is not included in this.
    """
    for name, class_ in Input.APIS.items():
        print(name, type(class_))
        yield class_.on_event(date_time=date_time)


def post_event(entry: Entry) -> None:
    """
    Execute the actions after the "pop-up" event.
    """
    for name, class_ in Output.APIS.items():
        print(name, type(class_))
        class_.post_event(entry=entry)
