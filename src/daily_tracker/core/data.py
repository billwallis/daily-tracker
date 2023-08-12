"""
Classes to hold and manipulate data needed throughout the application.
"""
import dataclasses
import datetime


@dataclasses.dataclass
class Task:
    """
    A task/project.

    This has corresponding details, a priority, and a flag to indicate whether
    it's a default task or not.
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
