"""
Handlers to work as the bridge between the form and the connectors.

This is specifically for the Form defined in this project so is purposefully
coupled to it.
"""
import abc
import csv
import datetime
import logging
import pathlib
from typing import Any, Protocol

import daily_tracker.core.configuration
import daily_tracker.core.database
import daily_tracker.integrations
import daily_tracker.integrations.calendars

DEBUG_MODE = False


def read_sql(
    sql: str,
    con: daily_tracker.core.database.DatabaseConnector,
    params: dict,
) -> list[tuple[Any, ...]]:
    """
    Return the result set from running SQL on a database connection.
    """
    with con.connection as conn:
        results = conn.execute(sql, params)

    return results.fetchall()


def to_csv(data: list[tuple[Any, ...]], path: pathlib.Path) -> None:
    """
    Write the data to a CSV file.
    """
    with open(path, "w", newline="") as out:
        csv.writer(out).writerows(data)


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

    def __init__(self, database_filepath: str):
        logging.debug(f"Loading database file at {database_filepath}...")
        self.connection = daily_tracker.core.database.DatabaseConnector(
            database_filepath
        )

    def ok_actions(
        self,
        configuration: daily_tracker.core.configuration.Configuration,
        form: Form,
    ) -> None:
        """
        The database actions that need to be executed when the OK button on the
        form is clicked.
        """
        logging.debug("Doing database actions...")
        if DEBUG_MODE:
            return

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
        output = read_sql(
            sql=latest_tasks,
            con=self.connection,
            params={"date_modifier": f"-{show_last_n_weeks * 7} days"},
        )

        return dict(output)  # type: ignore

    def get_last_task_and_detail(self) -> tuple[str, str]:
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
            {"task": task},
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
                },
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
        result = read_sql(
            sql=tracker_history,
            con=self.connection,
            params={"date_modifier": f"-{previous_days} days"},
        )
        headers = [("date_time", "task", "detail", "interval")]
        to_csv(
            data=headers + result,
            path=pathlib.Path(filepath)
            / f"daily-tracker-{datetime.datetime.now().strftime('%Y-%m-%d')}.csv",
        )

    def truncate_tables(self) -> None:
        """
        Truncate the tables in the database that are updated through the form.
        """
        for table in ["tracker", "task_last_detail"]:
            self.connection.truncate_table(table_name=table)
        self.connection.connection.commit()
