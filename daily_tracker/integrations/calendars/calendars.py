"""
Calendar types available to use for linking.
"""

import abc
import dataclasses
import datetime

import core


@dataclasses.dataclass
class CalendarEvent:
    """
    A calendar event, typically referred to as a _meeting_ or an _appointment_.
    """

    subject: str
    start: datetime.datetime
    end: datetime.datetime
    categories: set[str]
    all_day_event: bool


class Calendar(abc.ABC):
    """
    Abstraction of the various calendar types that can be synced with the daily
    tracker.
    """

    def __init__(self, configuration: core.Configuration):
        self.configuration = configuration

    @abc.abstractmethod
    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list[CalendarEvent]:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime exclusive.
        """

    @abc.abstractmethod
    def get_appointment_at_datetime(  # TODO: Rename this to `get_appointments_at_datetime`
        self,
        at_datetime: datetime.datetime,
    ) -> list[CalendarEvent]:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """

    def on_event(self, at_datetime: datetime.datetime) -> list[core.Task]:
        """
        Get the current meeting from Outlook if one exists.

        This excludes meetings that are daily meetings and meetings whose
        categories are in the supplied list of exclusions.
        """
        if not self.configuration.use_calendar_appointments:
            return []

        events = [
            event
            for event in self.get_appointment_at_datetime(
                at_datetime=at_datetime
            )
            if not event.all_day_event
            and all(
                i not in event.categories
                for i in self.configuration.appointment_category_exclusions
            )
        ]

        return [
            core.Task(
                task_name="Meetings",
                details=events[0].subject if len(events) == 1 else [],
            )
        ]

    def post_event(self, entry: core.Entry) -> None:
        """
        Temporarily here to allow for backwards compatibility.
        """
        pass


class NoCalendar(Calendar, core.Input, core.Output):
    """
    A 'None' calendar.
    """

    def __bool__(self):
        return False

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime exclusive.
        """
        return []

    def get_appointment_at_datetime(
        self,
        at_datetime: datetime.datetime,
        categories_to_exclude: list[str] = None,
    ) -> list:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """
        return []

    def on_event(self, at_datetime: datetime.datetime) -> list[core.Task]:
        return []

    def post_event(self, entry: core.Entry) -> None:
        pass
