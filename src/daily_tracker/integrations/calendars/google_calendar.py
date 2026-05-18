"""
Connect to and read events from a Gmail calendar.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
from typing import Any

import google.auth.exceptions
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import httplib2.error
from google.auth.transport import requests
from google.oauth2 import credentials

from daily_tracker import core, utils
from daily_tracker.integrations.calendars.calendars import (
    Calendar,
    CalendarEvent,
    EventResponse,
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
            # This raises `google.auth.exceptions.TransportError` if no internet
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


def _parse_datetime(dt_dct: dict[str, str]) -> datetime.datetime:
    dt_str = dt_dct.get("dateTime", dt_dct.get("date"))
    if dt_str is None:
        raise ValueError(
            f"Events needs a start and end time. Could not find `dateTime` or `date` in:\n{json.dumps(dt_dct, indent=2)}"
        )

    return datetime.datetime.fromisoformat(dt_str).replace(tzinfo=None)


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
        response = {
            "accepted": EventResponse.ACCEPTED,
            "declined": EventResponse.DECLINED,
            "tentative": EventResponse.TENTATIVE,
            "needsAction": EventResponse.TENTATIVE,
        }[
            next(
                (
                    attendee["responseStatus"]
                    for attendee in event.get("attendees", [])
                    if attendee.get("self", False)
                ),
                "accepted",  # no attendees => solo event
            )
        ]

        return GoogleCalendarEvent(
            subject=event["summary"],
            start=_parse_datetime(event_start),
            end=_parse_datetime(event_end),
            categories=set(category),
            all_day_event=all_day,
            response=response,
        )


class GoogleCalendar(Calendar, core.Input):
    """
    Naive implementation of a connector to a Google Calendar.
    """

    def __init__(self, configuration: core.Configuration) -> None:
        super().__init__(configuration=configuration)
        try:
            self.service = googleapiclient.discovery.build(
                serviceName="calendar",
                version="v3",
                credentials=get_credentials(),
            )
        except google.auth.exceptions.TransportError:
            self.service = None

    def get_appointments_between_datetimes(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
    ) -> list[GoogleCalendarEvent]:
        """
        Return the events in the calendar between the start datetime (inclusive)
        and end datetime exclusive.
        """

        if not self.service:
            return []

        # The Google API needs timezone-aware timestamps
        start_datetime = start_datetime.astimezone()
        end_datetime = end_datetime.astimezone()

        events_request = self.service.events().list(
            calendarId="primary",
            timeMin=start_datetime.isoformat(),
            timeMax=end_datetime.isoformat(),
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        try:
            events_result = events_request.execute()
        except (
            TimeoutError,
            httplib2.error.ServerNotFoundError,
        ):
            return []

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


if __name__ == "__main__":
    gcal = GoogleCalendar(core.Configuration.from_default())
    now = datetime.datetime.now()
    events = gcal.get_appointments_between_datetimes(
        start_datetime=now,
        end_datetime=now + datetime.timedelta(hours=8),
    )

    for event_ in events:
        print(event_)
