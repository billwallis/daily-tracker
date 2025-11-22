"""
Calendar types available to use for linking.
"""

from __future__ import annotations

import abc
import dataclasses
import datetime
import logging

from daily_tracker import core

logger = logging.getLogger("integrations")


def _filter_appointments(
    events: list[CalendarEvent],
    categories_to_exclude: list[str],
) -> list:
    """
    Filter out the appointments that are all day events or are in the
    exclusion list.
    """
    return [
        event
        for event in events
        if not event.all_day_event
        and all(i not in event.categories for i in categories_to_exclude)
    ]


@dataclasses.dataclass
class CalendarEvent:
    """
    A calendar event, typically referred to as a meeting or an appointment.
    """

    subject: str
    start: datetime.datetime
    end: datetime.datetime
    categories: set[str]
    all_day_event: bool


class Calendar(abc.ABC):
    """
    Abstraction of the various calendar types that can be synced with the
    daily tracker.
    """

    def __init__(self, configuration: core.Configuration) -> None:
        self.configuration = configuration

    @abc.abstractmethod
    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list[CalendarEvent]:
        """
        Return the events in the calendar between the start datetime
        (inclusive) and end datetime exclusive.
        """

    @abc.abstractmethod
    def get_appointments_at_datetime(
        self,
        at_datetime: datetime.datetime,
    ) -> list[CalendarEvent]:
        """
        Return the events in the calendar that are scheduled to on or over
        the supplied datetime.
        """

    def on_event(self, at_datetime: datetime.datetime) -> list[core.Task]:
        """
        Get the current meeting from Outlook if one exists.

        This excludes meetings that are daily meetings and meetings whose
        categories are in the supplied list of exclusions.
        """

        events = _filter_appointments(
            events=self.get_appointments_at_datetime(at_datetime=at_datetime),
            categories_to_exclude=self.configuration.appointment_category_exclusions,
        )
        s = "s" if len(events) != 1 else ""
        logger.debug(
            f"Found {len(events)} calendar event{s} for {at_datetime}."
        )

        if events:
            return [
                core.Task(
                    task_name="Meetings",
                    details=[event.subject for event in events],
                )
            ]

        return []

    def post_event(self, entry: core.Entry) -> None:
        """
        Do nothing.
        """
        logger.debug(
            f"No post-event actions for the calendar with entry {entry}."
        )


class NoCalendar(Calendar, core.Input, core.Output):
    """
    A 'None' calendar.
    """

    def __bool__(self) -> bool:
        return False

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list:
        """
        Return an empty list.
        """
        logger.debug(
            "Calling 'get_appointments_between_datetimes' for NoCalendar..."
        )
        return []

    def get_appointments_at_datetime(
        self,
        at_datetime: datetime.datetime,
        categories_to_exclude: list[str] | None = None,
    ) -> list:
        """
        Return an empty list.
        """
        logger.debug("Calling 'get_appointments_at_datetime' for NoCalendar...")
        return []
