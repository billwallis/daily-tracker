"""
The core backend of the daily tracker application.
"""
from core.apis import Input, Output
from core.configuration import Configuration
from core.data import Entry, Task
from core.scheduler import IndefiniteScheduler

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
