"""
All integrations supported by the application.

These aren't required for the application to run, but they add some
additional functionality.
"""

from integrations.calendars import Calendar
from integrations.jira import Jira
from integrations.slack import Slack

__all__ = [
    "Calendar",
    "Jira",
    "Slack",
]
