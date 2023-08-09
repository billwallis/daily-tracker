"""
Calendar types available to use for linking.
"""
import datetime
from typing import Protocol

import daily_tracker


class Calendar(Protocol):
    """
    Abstraction of the various calendar types that can be synced with the daily
    tracker.
    """

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime exclusive.
        """
        ...

    def get_appointments_at_datetime(
        self,
        at_datetime: datetime.datetime,
    ) -> list:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """
        ...


class NoCalendar(Calendar):
    """
    A 'None' calendar.
    """

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

    def get_appointments_at_datetime(
        self,
        at_datetime: datetime.datetime,
    ) -> list:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """
        return []


def get_linked_calendar(calendar_type: str) -> Calendar:
    """
    Convert the input calendar type string to the concrete representation of the
    class.
    """
    calendars = {
        "none": NoCalendar,
        "outlook": daily_tracker.integrations.calendars.OutlookConnector,
        # "gmail": daily_tracker.integrations.calendars.GmailConnector,
    }
    calendar = calendars.get(calendar_type)
    if calendar is None:
        raise NotImplementedError(
            f"The tracker currently does not support connections to {calendar}. Please use one of the following "
            f"instead: {','.join(calendars.keys())}"
        )

    return calendar()
