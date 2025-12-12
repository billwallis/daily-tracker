"""
All integrations supported by the application.

These aren't required for the application to run, but they add some
additional functionality.
"""

from daily_tracker.integrations.calendars import Calendar
from daily_tracker.integrations.github import GitHub
from daily_tracker.integrations.jira import Jira
from daily_tracker.integrations.monday import Monday
from daily_tracker.integrations.slack import Slack

__all__ = [
    "Calendar",
    "GitHub",
    "Jira",
    "Monday",
    "Slack",
]
