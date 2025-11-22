"""
Connect to and read events from a Gmail calendar.
"""

from __future__ import annotations

import dataclasses
import datetime
from typing import Any

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport import requests
from google.oauth2 import credentials

from daily_tracker import core, utils
from daily_tracker.integrations.calendars.calendars import (
    Calendar,
    CalendarEvent,
)

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = utils.ROOT / "credentials.json"
TOKEN_FILE = utils.ROOT / "token.json"
NO_CATEGORY = "-1"


def get_credentials() -> credentials.Credentials:
    """
    Authenticate the user and return Google API credentials.

    Taken from:

    - https://developers.google.com/workspace/calendar/api/quickstart/python#configure_the_sample
    """

    if TOKEN_FILE.exists():
        creds = credentials.Credentials.from_authorized_user_file(
            filename=str(TOKEN_FILE),
            scopes=SCOPES,
        )
    else:
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file=str(CREDENTIALS_FILE),
                scopes=SCOPES,
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        TOKEN_FILE.write_text(creds.to_json())

    return creds


@dataclasses.dataclass
class GoogleCalendarEvent(CalendarEvent):
    """
    A Google Calendar event.
    """

    @classmethod
    def from_event(cls, event: Any) -> GoogleCalendarEvent:
        """
        Create a ``GoogleCalendarEvent`` from a Google event.
        """

        category = [event.get("colorId", NO_CATEGORY)]
        event_start, event_end = event["start"], event["end"]
        all_day = event["start"].get("date") is not None

        return GoogleCalendarEvent(
            subject=event["summary"],
            start=event_start.get("dateTime") or event_start.get("date"),
            end=event_end.get("dateTime") or event_end.get("date"),
            categories=set(category),
            all_day_event=all_day,
        )


class GoogleCalendar(Calendar, core.Input):
    """
    Naive implementation of a connector to a Google Calendar.
    """

    def __init__(self, configuration: core.Configuration) -> None:
        super().__init__(configuration=configuration)
        self.service = googleapiclient.discovery.build(
            serviceName="calendar",
            version="v3",
            credentials=get_credentials(),
        )

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list[GoogleCalendarEvent]:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime exclusive.
        """

        # The Google API needs timezone-aware timestamps
        start_datetime = start_datetime.astimezone()
        end_datetime = end_datetime.astimezone()

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=start_datetime.isoformat(),
                timeMax=end_datetime.isoformat(),
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        return [
            GoogleCalendarEvent.from_event(e)
            for e in events_result.get("items", [])
        ]

    def get_appointments_at_datetime(
        self,
        at_datetime: datetime.datetime,
    ) -> list[GoogleCalendarEvent]:
        """
        Return the events in the calendar that are scheduled to on or over the
        supplied datetime.
        """

        return self.get_appointments_between_datetimes(
            start_datetime=at_datetime,
            end_datetime=at_datetime + datetime.timedelta(seconds=1),
        )
