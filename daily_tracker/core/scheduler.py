"""
The scheduler, which is responsible for scheduling the events.
"""
import datetime
import logging
import sched
import time
from collections.abc import Callable
from typing import Any

import core

Action = Callable[[datetime.datetime], Any]


def _get_interval_from_configuration() -> int:
    """
    Get the interval time from the configuration file.

    It's important to re-call this so that updates to the configuration file
    while the scheduler is running can be reflected in the scheduled events.
    """
    return core.Configuration.from_default().interval


def get_next_interval(
    from_time: datetime.datetime,
    interval_in_minutes: int,
) -> datetime.datetime:
    """
    Derive the next schedule time from the input time and interval.

    Schedules will be defined assuming that the schedule starts on the hour.
    This means that interval values that divide 60 will function the best.

    :param from_time: The datetime from which the scheduled datetime should be
        calculated. The scheduled datetime will be greater than or equal to this
        value.
    :param interval_in_minutes: The interval, in minutes, between the scheduled
        events.

    :return: The next scheduled datetime.
    """
    return datetime.timedelta(minutes=interval_in_minutes) + datetime.datetime(
        year=from_time.year,
        month=from_time.month,
        day=from_time.day,
        hour=from_time.hour,
        minute=from_time.minute - (from_time.minute % interval_in_minutes),
        second=0,
    )


class IndefiniteScheduler:
    """
    A processor that schedules the pop-up boxes and passes the data around to
    various applications indefinitely.
    """

    _interval: int
    _next_schedule_time: datetime.datetime
    _next_event: sched.Event | None
    _running: bool
    _scheduler: sched.scheduler
    action: Action

    def __init__(self, action: Action):
        """
        Create the scheduler to call the ``action`` on a schedule.

        The interval over which the schedule runs is defined in the
        configuration file.

        :param action: The function to call when the schedule is executed.
        """
        self._interval = _get_interval_from_configuration()
        self._running = False
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self.action = action

    def _action_wrapper(self) -> None:
        """
        Wrap the action so that we can schedule the next event when it's called.
        """
        self.action(self._next_schedule_time)
        self._interval = _get_interval_from_configuration()
        self._schedule_next()

    def _schedule(self, cancel: bool = False) -> None:
        """
        Schedule (or cancel) the next event.
        """
        if cancel:
            self._scheduler.cancel(self._next_event)
            self._next_event = None
        else:
            self._next_event = self._scheduler.enterabs(
                time=self._next_schedule_time.timestamp(),
                priority=1,
                action=self._action_wrapper,
            )

    def _schedule_next(self) -> None:
        """
        Schedule the next event.
        """
        assert self._running

        self._next_schedule_time = get_next_interval(
            from_time=self._next_schedule_time,
            interval_in_minutes=self._interval,
        )
        self._schedule()
        logging.debug(f"Next event scheduled for {self._next_schedule_time}")

    def _cancel_next(self) -> None:
        """
        Cancel the next event.
        """
        self._schedule(cancel=True)
        self._running = False

    def schedule_first(
        self,
        schedule_at: datetime.datetime = datetime.datetime.now(),
    ) -> None:
        """
        Schedule the first event.
        """
        assert not self._running, "The scheduler is already running."

        self._running = True
        self._next_schedule_time = schedule_at
        self._schedule_next()
        self._scheduler.run()
