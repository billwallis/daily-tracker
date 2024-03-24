# sourcery skip: upper-camel-case-classes,snake-case-variable-declarations
"""
The API classes that all integration classes should inherit from.

This module categorises all objects as ``Input`` and ``Output`` objects:

- The ``Input`` objects have an ``on_event`` method which is called
  before the task input is requested from the user.
- The ``Output`` objects have a ``post_event`` method which is called
  after the task input has been received from the user.

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

The backend will then only interact with the ``Input`` and ``Output``
type classes through the corresponding ``apis`` class property::

    >>> type(Input.apis), type(Output.apis)
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
import dataclasses
import datetime
import itertools
import logging
from typing import ClassVar

import core
import utils

logger = logging.getLogger("core")


class API(abc.ABC):
    """
    Implementation to automatically bind the integration objects to the
    ``Input`` and ``Output`` objects' ``apis`` class property.
    """

    apis: ClassVar[dict[str, API]]

    @classmethod
    def __new__(cls, *args, **kwargs):
        """
        During the initialisation of the subclass, use some metaprogramming to
        automatically bind the subclass to the ``Input`` and ``Output`` classes
        ``apis`` property.
        """
        instance = super().__new__(cls)
        key = utils.pascal_to_snake(cls.__name__)

        for base in cls.__bases__:
            if issubclass(base, API):
                logger.debug(
                    f"Adding class {instance} to `{base}.apis` with key '{key}'"
                )
                base.apis[key] = instance
        return instance


class IInput(abc.ABC):
    """
    Abstract base class for objects whose methods need to be actioned when
    the "pop-up" event starts.
    """

    @abc.abstractmethod
    def on_event(self, date_time: datetime.datetime) -> list[core.Task]:
        """
        The actions to perform at the start of the "pop-up" event at the
        scheduled time.
        """


class IOutput(abc.ABC):
    """
    Abstract base class for objects whose methods need to be resolved after the
    "pop-up" event ends.
    """

    @abc.abstractmethod
    def post_event(self, entry: core.Entry) -> None:
        """
        The actions to perform after the "pop-up" event.
        """


class Input(API, IInput, abc.ABC):
    """
    Abstract base class for objects whose methods need to be actioned when the
    "pop-up" event starts.
    """

    apis: ClassVar[dict[str, Input]] = {}

    @classmethod
    def on_events(
        cls,
        date_time: datetime.datetime,
    ) -> list[core.Task]:
        """
        Execute the actions at the start of the "pop-up" event.

        For the "pop-up" event, we need:

        1.  The default task and detail to show first
        2.  A list of alternative tasks that are available in the drop-down
        3.  A list of the latest details for each of the tasks from 2

        The UI call is only made after this -- and only if the UI is enabled as
        there could be other interfaces.
        """
        tasks = [
            object_.on_event(date_time=date_time)
            for name, object_ in cls.apis.items()
        ]
        return list(itertools.chain.from_iterable(tasks))


class Output(API, IOutput, abc.ABC):
    """
    Abstract base class for objects whose methods need to be resolved after the
    "pop-up" event ends.
    """

    apis: ClassVar[dict[str, Output]] = {}

    @classmethod
    def post_events(cls, entry: core.Entry) -> None:
        """
        Execute the actions after the "pop-up" event.
        """
        for name, object_ in Output.apis.items():
            object_.post_event(entry=entry)


@dataclasses.dataclass
class Task:
    """
    A task/project.

    This has corresponding details, a priority, and a flag to indicate
    whether it's a default task or not.
    """

    task_name: str
    details: list[str] = dataclasses.field(default_factory=list)
    priority: int = 1
    is_default: bool = False


@dataclasses.dataclass
class Entry:
    """
    An entry for the tracker.

    This has a timestamp, a task, a detail, and an interval.
    """

    date_time: datetime.datetime
    task_name: str
    detail: str
    interval: int
