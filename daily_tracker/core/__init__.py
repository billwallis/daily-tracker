"""
The core entities required to make the application function.
"""
from core.apis import Input, Output
from core.configuration import Configuration
from core.data import Entry, Task

__all__ = [
    "Input",
    "Output",
    "Configuration",
    "Entry",
    "Task",
]
