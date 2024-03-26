"""
Various calendar integrations.
"""

import os

import core
from integrations.calendars.calendars import Calendar, NoCalendar

# from integrations.calendars.gmail import GmailInput

if os.name == "nt":
    from integrations.calendars.outlook_windows import OutlookInput
elif os.name == "posix":
    from integrations.calendars.outlook_mac import OutlookInput


CALENDAR_LOOKUP = {
    "none": NoCalendar,
    # "gmail": GmailInput,
    "outlook": OutlookInput,
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


# Force into the Input/Output classes. This is naughty, but we'll fix it later
get_linked_calendar(core.configuration.Configuration.from_default())
