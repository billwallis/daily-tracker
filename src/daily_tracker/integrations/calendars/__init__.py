import sys

from daily_tracker import core
from daily_tracker.integrations.calendars.calendars import Calendar, NoCalendar
from daily_tracker.integrations.calendars.google_calendar import GoogleCalendar

if sys.platform == "win32":
    from daily_tracker.integrations.calendars.outlook_windows import Outlook
elif sys.platform == "darwin":
    from daily_tracker.integrations.calendars.outlook_mac import Outlook
else:
    from daily_tracker.integrations.calendars.calendars import (
        NoCalendar as Outlook,
    )


CALENDAR_LOOKUP = {
    "none": NoCalendar,
    "google": GoogleCalendar,
    "outlook": Outlook,
}


def get_linked_calendar(configuration: core.Configuration) -> Calendar:
    """
    Convert the input calendar type string to the concrete representation of the
    class.
    Currently, only using a single calendar type is supported.
    """

    calendar = CALENDAR_LOOKUP.get(configuration.linked_calendar)
    if calendar is None:
        raise NotImplementedError(
            f"The tracker currently does not support connections to {calendar}."
            f" The supported connections are:\n"
            f"{','.join(CALENDAR_LOOKUP.keys())}"
        )

    return calendar(configuration)
