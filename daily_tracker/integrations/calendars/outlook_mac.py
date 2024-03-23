"""
Connect to and read events from an Outlook calendar.

This requires Outlook to be installed as a desktop application on the
device running this code, and for it to be toggled to the old version of
Outlook ("old" as at 2023-01-10).

This is powered by the appscript library which is super helpful, but
there are some features missing in Outlook on macOS that are available
in Outlook on Windows. For example, there is no "all-day" flag in the
macOS version, and recurring events only show the initial event but not
the subsequent ones.

The use of appscript has been adapted from:

- https://stackoverflow.com/a/62089384/8213085


Additional appscript usage has been determined from using the
ASTranslate tool, available at:

- https://sourceforge.net/projects/appscript/files/
"""

from __future__ import annotations

import dataclasses
import datetime

import appscript
from appscript.reference import Reference

import core
from integrations.calendars.calendars import Calendar, CalendarEvent


@dataclasses.dataclass
class OutlookEvent(CalendarEvent):
    """
    An Outlook event corresponding to macOS.
    """

    @classmethod
    def from_appointment(cls, appointment: Reference) -> OutlookEvent:
        """
        Generate an OutlookEvent from a macOS Outlook appointment.

        :param appointment: The appscript appointment to generate the event
         from.
        """
        return OutlookEvent(
            subject=appointment.subject.get(),
            start=appointment.start_time.get(),
            end=appointment.end_time.get(),
            categories={cat.name.get() for cat in appointment.category.get()},
            all_day_event=appointment.start_time.get().hour == 0,
        )


class OutlookInput(Calendar, core.Input):
    """
    Naive implementation of a connector to Outlook on macOS.
    """

    def __init__(self, configuration: core.Configuration):
        super().__init__(configuration=configuration)

        # TODO: Set the calendar ID dynamically rather than hard-coding it
        self.calendar = appscript.app("Microsoft Outlook").calendars.ID(110)

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list[OutlookEvent]:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime (exclusive).
        """
        restricted_calendar = self.calendar.calendar_events[
            (appscript.its.start_time >= start_datetime).AND(
                appscript.its.end_time < end_datetime
            )
        ].get()
        return [
            OutlookEvent.from_appointment(app) for app in restricted_calendar
        ]

    def get_appointment_at_datetime(
        self,
        at_datetime: datetime.datetime,
    ) -> list[OutlookEvent]:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """
        restricted_calendar = self.calendar.calendar_events[
            (appscript.its.start_time <= at_datetime).AND(
                appscript.its.end_time > at_datetime
            )
        ].get()
        return [
            OutlookEvent.from_appointment(app) for app in restricted_calendar
        ]
