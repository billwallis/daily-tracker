"""
Connect to and read events from an Outlook calendar.

This requires Outlook to be installed as a desktop application on the
device running this code and is powered by the win32com library.
"""

from __future__ import annotations

import dataclasses
import datetime

import win32com.client  # noqa
from win32com.client import CDispatch  # noqa

import core
import utils
from integrations.calendars.calendars import Calendar, CalendarEvent


@dataclasses.dataclass
class OutlookEvent(CalendarEvent):
    """
    An Outlook event corresponding to Windows.
    """

    @classmethod
    def from_appointment(cls, appointment: CDispatch) -> OutlookEvent:
        """
        Generate an OutlookEvent from a Windows Outlook appointment.

        :param appointment: The win32com appointment to generate the event from.
        """
        return OutlookEvent(
            subject=appointment.subject,
            start=appointment.start,
            end=appointment.end,
            categories=set(utils.string_list_to_list(appointment.categories)),
            all_day_event=appointment.all_day_event,
        )


class Outlook(Calendar, core.Input):
    """
    Naive implementation of a connector to Outlook on Windows.
    """

    def __init__(self, configuration: core.Configuration):
        # sourcery skip: docstrings-for-functions
        super().__init__(configuration=configuration)

        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        self.calendar = outlook.getDefaultFolder(9).Items
        self.calendar.IncludeRecurrences = True
        self.calendar.Sort("[Start]")

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list[OutlookEvent]:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime exclusive.
        """
        restricted_calendar = self.calendar.Restrict(
            " AND ".join(
                [
                    f"[Start] >= '{start_datetime.strftime('%Y-%m-%d %H:%M')}'",
                    f"[END] < '{end_datetime.strftime('%Y-%m-%d %H:%M')}'",
                ]
            )
        )
        return [OutlookEvent.from_appointment(app) for app in restricted_calendar]

    def get_appointments_at_datetime(
        self,
        at_datetime: datetime.datetime,
    ) -> list[OutlookEvent]:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """
        datetime_string = at_datetime.strftime("%Y-%m-%d %H:%M")
        restricted_calendar = self.calendar.Restrict(
            " AND ".join(
                [
                    f"[Start] <= '{datetime_string}'",
                    f"[END] > '{datetime_string}'",
                ]
            )
        )
        return [OutlookEvent.from_appointment(app) for app in restricted_calendar]
