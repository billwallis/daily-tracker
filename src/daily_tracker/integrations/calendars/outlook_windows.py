"""
Connect to and read events from an Outlook calendar.

This requires Outlook to be installed as a desktop application on the device
running this code.
"""
import dataclasses
import datetime

import win32com.client

import daily_tracker.utils


@dataclasses.dataclass
class OutlookEvent:
    """
    Events in Outlook, typically referred to as Meetings or Appointments.

    Note that categories are not available for IMAP accounts, see:
        * https://learn.microsoft.com/en-us/outlook/troubleshoot/user-interface/cannot-assign-color-categories-for-imap-accounts
    """

    _appointment: win32com.client.CDispatch = dataclasses.field(repr=False)
    subject: str = dataclasses.field(default=None)
    start: datetime.datetime = dataclasses.field(default=None)
    end: datetime.datetime = dataclasses.field(default=None)
    body: str = dataclasses.field(default=None)
    categories: list[str] = dataclasses.field(default=list)

    def __post_init__(self):
        """
        Pull out the appointment details into fields.
        """
        self.subject = self._appointment.subject
        self.start = self._appointment.start
        self.end = self._appointment.end
        self.body = self._appointment.body
        self.categories = daily_tracker.utils.string_list_to_list(
            self._appointment.categories
        )


class OutlookConnector:
    """
    Naive implementation of a connector to Outlook.
    """

    def __init__(self):
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
        return [OutlookEvent(app) for app in restricted_calendar]

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
        return [OutlookEvent(app) for app in restricted_calendar]
