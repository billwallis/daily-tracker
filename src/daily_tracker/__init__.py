"""
The core backend of the daily tracker application.
"""
from daily_tracker.core.apis import Input, Output, on_event, post_event
from daily_tracker.core.configuration import Configuration
from daily_tracker.core.data import Entry, Task
from daily_tracker.core.database.database import DatabaseHandler
from daily_tracker.core.scheduler import IndefiniteScheduler

__all__ = [
    # Abstract integration APIs
    "Input",
    "Output",
    "on_event",
    "post_event",
    # Tracker configuration/options
    "Configuration",
    # Data classes
    "Entry",
    "Task",
    # Scheduler
    "IndefiniteScheduler",
]
