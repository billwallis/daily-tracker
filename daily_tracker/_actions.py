"""
The actions for the pop-up box.
"""
import datetime
import os.path

import dotenv

import core
import core.database
import core.form
import integrations
import tracker_utils

dotenv.load_dotenv(dotenv_path=r".env")
JIRA_CREDENTIALS = {
    "domain": os.getenv("JIRA_DOMAIN"),
    "key": os.getenv("JIRA_KEY"),
    "secret": os.getenv("JIRA_SECRET"),
}
SLACK_CREDENTIALS = {
    "url": os.getenv("SLACK_WEBHOOK_URL"),
}


class ActionHandler:
    """
    Handler for the actions that are triggered on the pop-up box.
    """

    def __init__(self, at_datetime: datetime.datetime):
        """
        Initialise the main handler and the various handlers to other systems.
        """
        self.configuration = core.Configuration.from_default()
        self.database_handler = core.database.DatabaseHandler(
            tracker_utils.DB,
            configuration=self.configuration,
        )
        self.calendar_handler = integrations.get_linked_calendar(
            self.configuration.linked_calendar
        )(self.configuration)
        self.jira_handler = integrations.Jira(
            **JIRA_CREDENTIALS,
            configuration=self.configuration,
        )
        self.slack_handler = integrations.Slack(
            **SLACK_CREDENTIALS,
            configuration=self.configuration,
        )
        self.form = core.form.TrackerForm(
            at_datetime=at_datetime,
            action_handler=self,
        )

        self.form.generate_form()

    def ok_actions(self) -> None:
        """
        The actions to perform after the "pop-up" event.
        """
        for handler in [
            self.database_handler,  # This needs to be done first
            self.calendar_handler,
            self.slack_handler,
            self.jira_handler,
        ]:
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

    def get_default_task_and_detail(
        self,
        at_datetime: datetime.datetime,
    ) -> tuple[str, str]:
        """
        Get the default values for the input box.

        This takes the meeting details from the linked calendar (if one has been
        linked), or just uses the latest task.
        """
        current_meeting = self.calendar_handler.get_appointment_at_datetime(
            at_datetime=at_datetime,
            categories_to_exclude=self.configuration.appointment_category_exclusions,
        )

        if (
            not self.configuration.use_calendar_appointments
            or current_meeting is None
        ):
            return self.database_handler.get_last_task_and_detail(
                datetime.datetime.now()
            ) or ("", "")
        return "", ""

    def get_dropdown_options(self, use_jira_sprint: bool) -> dict:
        """
        Return the latest tasks and their most recent detail as a dictionary.

        This is always the most recent tasks, and optionally the tickets in the
        active sprint if a Jira connection has been configured.
        """
        recent_tasks = self.database_handler.get_recent_tasks(
            self.configuration.show_last_n_weeks
        )

        if use_jira_sprint:
            recent_tickets = [
                ticket
                for ticket in self.jira_handler.get_tickets_in_sprint()
                if ticket not in recent_tasks.keys()
            ]
        else:
            recent_tickets = []

        return {
            **recent_tasks,
            **dict.fromkeys(recent_tickets, ""),
        }
