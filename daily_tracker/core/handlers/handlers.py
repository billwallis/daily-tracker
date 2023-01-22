"""
Handlers to work as the bridge between the form and the connectors.

This is specifically for the Form defined in this project so is purposefully
coupled to it.
"""
import abc
import datetime
import json
import os
import re
from typing import List, Tuple, Optional
from typing_extensions import Protocol

import pandas as pd

import daily_tracker.core.configuration
import daily_tracker.core.database
import daily_tracker.integrations
import daily_tracker.integrations.calendars


DEBUG_MODE = False


class Form(Protocol):
    """
    The handlers need properties from the form to be able to pass the details
    around for the various methods.
    """
    task: str
    detail: str
    at_datetime: datetime.datetime
    interval: int


class Handler(abc.ABC):
    """
    Handles the actions to execute on the form for a given connector to another
    tool/software.
    """

    @abc.abstractmethod
    def ok_actions(
        self,
        configuration: daily_tracker.core.configuration.Configuration,
        form: Form,
    ) -> None:
        """
        Actions to execute when the OK button is pressed on the form.
        """
        pass


class DatabaseHandler(Handler):
    """
    Handle the connection to the backend database.
    """
    def __init__(self, database_filepath):
        self.connection = daily_tracker.core.database.DatabaseConnector(database_filepath)

    def ok_actions(
        self,
        configuration: daily_tracker.core.configuration.Configuration,
        form: Form,
    ) -> None:
        """
        The database actions that need to be executed when the OK button on the
        form is clicked.
        """
        if DEBUG_MODE:
            print("Doing database actions...")
        else:
            self._write_to_database(
                task=form.task,
                detail=form.detail,
                at_datetime=form.at_datetime,
                interval=form.interval,
            )

            # Only extract data on the hour -- consider making this more flexible
            if form.at_datetime.minute == 0 and configuration.save_csv_copy:
                self.write_to_csv(filepath=configuration.csv_filepath)

    def get_recent_tasks(self, show_last_n_weeks: int) -> dict:
        """
        Return the drop-down list of recent tasks.

        This takes the result of a query into a dataframe, and then converts the
        dataframe into a dictionary whose keys are the tasks and the values are
        the task's latest detail.
        """
        latest_tasks = """
            SELECT task, detail
            FROM task_detail_with_defaults
            WHERE last_date_time >= DATETIME('now', :date_modifier)
               OR indx = 0  /* Defaults */
            ORDER BY indx, task
        """
        return dict(
            pd.read_sql(
                sql=latest_tasks,
                con=self.connection.engine,
                params={"date_modifier": f"-{show_last_n_weeks * 7} days"},
            ).to_dict("split")["data"]
        )

    def get_last_task_and_detail(self) -> Tuple[str, str]:
        """
        Return the most recent task and its detail.
        """
        with self.connection.connection as conn:
            return conn.execute(
                """
                SELECT task, detail
                FROM tracker
                ORDER BY date_time DESC
                LIMIT 1
                """
            ).fetchone()

    def get_details_for_task(self, task: str) -> list:
        """
        Return the list of recent detail for the task.

        TODO: Use memoisation to avoid repeated queries to the DB.
        """
        details = self.connection.execute(
            """
            SELECT detail
            FROM tracker
            WHERE task = :task
            GROUP BY detail
            ORDER BY MAX(date_time) DESC
            LIMIT 10
            """,
            {"task": task}
        ).fetchall()
        return [detail[0] for detail in details]

    def _write_to_database(
        self,
        task: str,
        detail: str,
        at_datetime: datetime.datetime,
        interval: int,
    ) -> None:
        """
        Write the form values to the database.
        """
        with self.connection.connection as conn:
            conn.execute(
                """
                INSERT INTO tracker(date_time, task, detail, interval)
                    VALUES (:at_datetime, :task, :detail, :interval)
                """,
                {
                    "at_datetime": at_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "task": task,
                    "detail": detail,
                    "interval": interval,
                }
            )

    def write_to_csv(self, filepath: str, previous_days: int = None) -> None:
        """
        Write the tracker history to a CSV file.

        By default, this will download the entire history. To limit this, set
        the number of days to limit this to with the `previous_days` parameter.
        """
        tracker_history = """
            SELECT
                date_time,
                task,
                detail,
                interval
            FROM tracker
            WHERE date_time >= DATE('now', :date_modifier)
            ORDER BY date_time
        """
        pd.read_sql(
            sql=tracker_history,
            con=self.connection.engine,
            params={"date_modifier": f"-{previous_days} days"},
        ).to_csv(
            os.path.join(
                filepath,
                f"daily-tracker-{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.csv"
            )
        )

    def truncate_tables(self) -> None:
        """
        Truncate the tables in the database that are updated through the form.
        """
        for table in ["tracker", "task_last_detail"]:
            self.connection.truncate_table(table_name=table)
        self.connection.connection.commit()

    def import_history(self, filepath: str) -> None:
        """
        Import the existing CSV file into the SQLite database.
        """
        column_names = {
            "Datetime": "date_time",
            "Task": "task",
            "Detail": "detail",
            "Interval": "interval",
        }
        data = (
            pd.read_csv(
                filepath_or_buffer=filepath,
                usecols=list(column_names),
                parse_dates=["Datetime"]
            )[list(column_names)]
            .rename(column_names, axis=1)
            .fillna("")
        )
        data["date_time"] = data["date_time"].dt.strftime("%Y-%m-%d %H:%M:%S")

        self.truncate_tables()
        with self.connection.connection as conn:
            conn.execute("""
                INSERT INTO task_last_detail(task, detail, last_date_time)
                    SELECT task, '', '' FROM default_tasks
            """)
        data.to_sql(
            name="tracker",
            con=self.connection.engine,
            if_exists="append",
            index=False,
        )


class CalendarHandler(Handler):
    """
    Handle the connection to the linked calendar.
    """
    def __init__(self, calendar_type: str):
        self.connection = daily_tracker.integrations.calendars.get_linked_calendar(calendar_type)

    def ok_actions(
        self,
        configuration: daily_tracker.core.configuration.Configuration,
        form: Form,
    ) -> None:
        """
        The calendar actions that need to be executed when the OK button on the
        form is clicked.
        """
        # sourcery skip: remove-redundant-pass
        if DEBUG_MODE:
            print("Doing calendar actions...")
        else:
            # Set status?
            # print("Create some calendar actions!")
            pass

    def get_appointment_at_datetime(
        self,
        at_datetime: datetime.datetime,
        categories_to_exclude: List[str],
    ) -> Optional[str]:
        """
        Get the current meeting from Outlook, if one exists.

        This excludes meetings that are daily meetings and meetings whose
        categories are in the supplied list of exclusions.
        """
        if categories_to_exclude is None:
            categories_to_exclude = []

        events = [
            event
            for event in self.connection.get_appointments_at_datetime(at_datetime=at_datetime)
            if all(i not in event.categories for i in categories_to_exclude)
               # and not event.all_day_event
               and event.start.hour != 0
        ]

        return None if len(events) != 1 else events[0].subject


class JiraHandler(Handler):
    """
    Handle the connection to the linked Jira project.
    """
    def __init__(self, url: str, key: str, secret: str):
        self.connector = daily_tracker.integrations.JiraConnector(
            url=url,
            key=key,
            secret=secret,
        )
        self.project_key_pattern = re.compile(r"^[A-Z]\w{1,9}-\d+")

    def ok_actions(
        self,
        configuration: daily_tracker.core.configuration.Configuration,
        form: Form,
    ) -> None:
        """
        The Jira actions that need to be executed when the OK button on the form
        is clicked.
        """
        # sourcery skip: merge-else-if-into-elif
        if DEBUG_MODE:
            print("Doing Jira actions...")
        else:
            if configuration.post_to_jira:
                self._post_log_to_jira(
                    task=form.task,
                    detail=form.detail,
                    at_datetime=form.at_datetime,
                    interval=form.interval
                )

    def _post_log_to_jira(
        self,
        task: str,
        detail: str,
        at_datetime: datetime.datetime,
        interval: int
    ) -> None:
        """
        Post the task, detail, and time to the corresponding ticket's worklog.
        """
        issue_key = re.search(self.project_key_pattern, task)
        if issue_key is None:
            return None

        self.connector.add_worklog(
            issue_key=issue_key[0],
            detail=detail,
            at_datetime=at_datetime.isoformat() + ".000+0000",
            interval=interval
        )

    def get_tickets_in_sprint(self, project_key: str = None) -> List[str]:
        """
        Get the list of tickets in the active sprint for the current user.
        """
        # Pretty sure there's a better way to do this
        if project_key:
            jql = f"project = {project_key} AND sprint IN openSprints() AND assignee = currentUser()"
        else:
            jql = "sprint IN openSprints() AND assignee = currentUser()"

        fields = ["summary", "duedate", "assignee"]

        def get_batch_of_tickets(start_at: int) -> dict:
            """
            Inner function to loop over until all tickets have been retrieved.
            """
            return json.loads(self.connector.search_for_issues_using_jql(
                jql=jql,
                fields=fields,
                start_at=start_at,
            ).text)

        results = []
        total = 999
        while len(results) < total:
            response = get_batch_of_tickets(start_at=len(results))
            total = response["total"]
            results += [f"{issue['key']} {issue['fields']['summary']}" for issue in response["issues"]]

        return results


class SlackHandler(Handler):
    """
    Handle the connection to the linked Slack workspace.
    """
    def __init__(self, url: str):
        self.connector = daily_tracker.integrations.SlackConnector(url)

    def ok_actions(
        self,
        configuration: daily_tracker.core.configuration.Configuration,
        form: Form,
    ) -> None:
        """
        The Slack actions that need to be executed when the OK button on the
        form is clicked.
        """
        # sourcery skip: merge-else-if-into-elif
        if DEBUG_MODE:
            print("Doing Slack actions...")
        else:
            if configuration.post_to_slack:
                self._post_to_channel(
                    task=form.task,
                    detail=form.detail
                )
                # Set status?

    def _post_to_channel(self, task: str, detail: str) -> None:
        """
        Post the task details to a channel.
        """
        self.connector.post_to_channel(message=f"*{task}*: {detail}")
