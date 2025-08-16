"""
The actions for the pop-up box.
"""

import datetime
import logging

from daily_tracker import core, integrations
from daily_tracker.core import database, form

logger = logging.getLogger("core")


class ActionHandler:
    """
    Handler for the actions that are triggered on the pop-up box.
    """

    def __init__(self, at_datetime: datetime.datetime):
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

    def get_default_task_and_detail(
        self,
        at_datetime: datetime.datetime,
    ) -> tuple[str, str]:
        """
        Get the default values for the input box.

        This takes the meeting details from the linked calendar (if one has been
        linked), or just uses the latest task.

        TODO: Replace with the ``on_event`` methods from the input classes.
        """
        calendar_handler: integrations.Calendar = self.inputs.get("calendar")  # type: ignore
        if calendar_handler and self.configuration.use_calendar_appointments:
            current_meetings = [
                meeting
                for meeting in calendar_handler.get_appointments_at_datetime(
                    at_datetime=at_datetime,
                )
                if not meeting.all_day_event
                and all(
                    i not in meeting.categories
                    for i in self.configuration.appointment_category_exclusions
                )
            ]
        else:
            current_meetings = []

        database_handler: database.Database = self.outputs["database"]  # type: ignore
        logger.debug(f"Using database {database_handler}.")
        if len(current_meetings) != 1:
            # If there are two events, we don't know which one to use so
            # default to the last task from the database instead
            return database_handler.get_last_task_and_detail(
                date_time=at_datetime
            ) or ("", "")

        assert len(current_meetings) == 1  # noqa: S101
        return "Meetings", current_meetings[0].subject

    def get_dropdown_options(self, jira_filter: str) -> dict[str, str]:
        """
        Return the latest tasks and their most recent detail as a dictionary.

        This is always the most recent tasks, and optionally the tickets in the
        active sprint if a Jira connection has been configured.
        """
        database_handler: database.Database = self.outputs["database"]  # type: ignore
        jira_handler: integrations.Jira = self.inputs.get("jira")  # type: ignore

        recent_tasks = database_handler.get_recent_tasks(
            self.configuration.show_last_n_weeks
        )
        if jira_handler and jira_filter:
            recent_tickets = [
                ticket
                for ticket in jira_handler.get_tickets_in_sprint()
                if ticket not in recent_tasks.keys()
            ]
        else:
            recent_tickets = []

        return {
            **recent_tasks,
            **dict.fromkeys(recent_tickets, ""),
        }

    def ok_actions(self) -> None:
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
            if hasattr(handler, "ok_actions"):
                # For backwards compatibility
                handler.ok_actions(self.configuration, self.form)
            else:
                entry = core.Entry(
                    date_time=self.form.at_datetime,
                    task_name=self.form.task,
                    detail=self.form.detail,
                    interval=self.form.interval,
                )
                handler.post_event(entry)
