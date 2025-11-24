"""
The actions for the pop-up box.
"""

import collections
import datetime
import logging

from daily_tracker import core, integrations
from daily_tracker.core import database, form

logger = logging.getLogger("core")


class ActionHandler:
    """
    Handler for the actions that are triggered on the pop-up box.
    """

    def __init__(self, at_datetime: datetime.datetime) -> None:
        """
        Initialise the main handler and the various handlers to other systems.
        """
        self.configuration = core.Configuration.from_default()
        # These only work because we cheat and instantiate the Input/Output
        # subclasses in their corresponding modules
        self.inputs = core.Input.apis
        self.outputs = core.Output.apis

        # Form
        self.form = form.TrackerForm(
            at_datetime=at_datetime,
            action_handler=self,
        )
        self.form.generate_form()

    def get_dropdown_options(
        self,
        jira_filter: str | None = None,
    ) -> dict[str, list[str]]:
        """
        Return the latest tasks and their most recent detail as a dictionary.

        This is always the most recent tasks, and optionally the tickets in the
        active sprint if a Jira connection has been configured.
        """

        database_handler: database.Database = self.outputs["database"]  # type: ignore
        jira_handler: integrations.Jira = self.inputs.get("jira")  # type: ignore
        monday_handler: integrations.Monday = self.inputs.get("monday")  # type: ignore

        tasks_and_details = collections.defaultdict(list)

        for task, detail in database_handler.get_recent_tasks(
            self.configuration.show_last_n_weeks
        ).items():
            tasks_and_details[task].append(detail)

        if jira_handler and jira_filter:
            for ticket in jira_handler.get_tickets_in_sprint():
                tasks_and_details[ticket].append("")

        if monday_handler:
            for subtask in monday_handler.on_event(
                date_time=datetime.datetime.now()
            ):
                tasks_and_details[subtask.task_name].extend(subtask.details)

        # deduplicate the details
        for task, details in tasks_and_details.items():
            tasks_and_details[task] = list(dict.fromkeys(details))

        return tasks_and_details

    def do_on_events(
        self,
        at_datetime: datetime.datetime,
    ) -> tuple[str, str]:
        """
        Get the default values for the input box.

        This takes the meeting details from the linked calendar (if one has been
        linked), or just uses the latest task.

        TODO: Replace with the ``on_event`` methods from the input classes.
        """

        (calendar_handler,) = [
            h
            for h in self.inputs.values()
            if isinstance(h, integrations.Calendar)
        ]
        current_meetings = calendar_handler.on_event(at_datetime)

        database_handler: database.Database = self.outputs["database"]  # type: ignore
        logger.debug(f"Using database {database_handler}.")
        if len(current_meetings) != 1:
            # If there are two events, we don't know which one to use so
            # default to the last task from the database instead
            fallback = ("", "")
            return (
                database_handler.get_last_task_and_detail(at_datetime)
                or fallback
            )

        (current_meeting,) = current_meetings
        return current_meeting.task_name, current_meeting.details[0]

    def do_post_events(self) -> None:
        """
        The actions to perform after the "pop-up" event.
        """
        # Dirty approach to get the database stuff done first
        outputs_ = [self.outputs["database"]] + [
            handler
            for name, handler in self.outputs.items()
            if name != "database"
        ]

        for handler in outputs_:
            entry = core.Entry(
                date_time=self.form.at_datetime,
                task_name=self.form.task,
                detail=self.form.detail,
                interval=self.form.interval,
            )
            handler.post_event(entry)
