"""
Maintain the backend SQLite database.
"""

import csv
import datetime
import logging
import pathlib
import sqlite3
from collections.abc import Mapping
from typing import Any

from daily_tracker import core, utils

logger = logging.getLogger("core")

DEBUG_MODE = False


class DatabaseConnector:
    """
    Connects to an SQLite database.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.connection = sqlite3.connect(self.filepath, timeout=15)
        self._create_backend()

    def execute(
        self,
        sql: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> sqlite3.Cursor:
        """
        Shortcut to the execute method on the SQLite connection object.
        """
        return self.connection.execute(sql, parameters)

    def run_query_from_file(self, filepath: str) -> sqlite3.Cursor:
        """
        Open a file and execute the query inside it.
        """
        with open(filepath) as f:
            return self.connection.executescript(f.read())

    def _create_backend(self) -> None:
        """
        Create the backend if it doesn't already exist.
        """
        if not (
            self.connection.execute(
                """
                select name
                from sqlite_master
                where type = 'table'
                  and name = 'tracker'
                """
            ).fetchone()
        ):
            self.run_query_from_file(
                utils.DAILY_TRACKER / "core/scripts/create.sql"
            )

    def truncate_table(self, table_name: str) -> None:
        """
        Truncate a table if it exists.
        """
        if self.connection.execute(
            """
                select name
                from sqlite_master
                where type = 'table'
                  and name = :table_name
                """,
            {"table_name": table_name},
        ).fetchone():
            self.connection.execute(
                f"""DELETE FROM {table_name} WHERE 1=1"""  # noqa: S608
            )


def read_sql(
    sql: str,
    con: DatabaseConnector,
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


class Database(core.Input, core.Output):
    """
    The database handler.

    This bridges the input and output objects with the database connector
    object to implement the input and output actions.
    """

    def __init__(
        self,
        database_filepath: str,
        configuration: core.Configuration,
    ):
        logger.debug(f"Loading database file at {database_filepath}...")
        self.connection = DatabaseConnector(database_filepath)
        self.configuration = configuration

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
        raise NotImplementedError(
            "'Database.import_history' has not been implemented."
        )
        # column_names = [
        #     "date_time",
        #     "task",
        #     "detail",
        #     "interval",
        # ]
        # data = (
        #     pd.read_csv(
        #         filepath_or_buffer=filepath,
        #         usecols=column_names,
        #         parse_dates=["date_time"]
        #     )[column_names]
        #     .fillna("")
        # )
        # data["date_time"] = data["date_time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        #
        # self.truncate_tables()
        # with self.connection.connection as conn:
        #     conn.execute(
        #         """
        #         INSERT INTO task_last_detail(task, detail, last_date_time)
        #             SELECT task, '', '' FROM default_tasks
        #         """
        #     )
        #
        # data.to_sql(
        #     name="tracker",
        #     con=self.connection.engine,
        #     if_exists="append",
        #     index=False,
        # )

    def on_event(self, date_time: datetime.datetime) -> list[core.Task]:
        """
        The actions to perform before the event.
        """
        latest_task_and_detail = self.get_last_task_and_detail(
            date_time=date_time
        )
        recent_tasks_with_defaults = self.get_recent_tasks_with_defaults(
            show_last_n_weeks=self.configuration.show_last_n_weeks
        ).items()

        return (
            []
            + [
                core.Task(
                    task_name=latest_task_and_detail[0],
                    details=[latest_task_and_detail[1]],
                    priority=0,
                )
            ]
            + [
                core.Task(
                    task_name=task,
                    details=[],
                    is_default=bool(default_flag),
                )
                for task, default_flag in recent_tasks_with_defaults
            ]
        )

    def get_last_task_and_detail(
        self,
        date_time: datetime.datetime,
    ) -> tuple[str, str]:
        """
        Return the most recent task and its detail.
        """
        with self.connection.connection as conn:
            return conn.execute(
                """
                select task, detail
                from tracker
                where date_time <= :date_time
                order by date_time desc
                limit 1
                """,
                {"date_time": date_time.strftime("%Y-%m-%d %H:%M:%S")},
            ).fetchone()

    def get_recent_tasks(self, show_last_n_weeks: int) -> dict[str, str]:
        """
        Return the drop-down list of recent tasks.

        This takes the result of a query into a dataframe, and then converts the
        dataframe into a dictionary whose keys are the tasks and the values are
        the task's latest detail.
        """
        # latest_tasks = """
        #     select task, detail
        #     from v_latest_tasks
        #     where last_date_time >= datetime('now', :date_modifier)
        #        or indx = 0  /* Defaults */
        #     order by indx, task
        # """
        latest_tasks = """
            select task, detail
            from task_detail_with_defaults
            where last_date_time >= datetime('now', :date_modifier)
               or indx = 0  /* Defaults */
            order by indx, task
        """
        output = read_sql(
            sql=latest_tasks,
            con=self.connection,
            params={"date_modifier": f"-{show_last_n_weeks * 7} days"},
        )

        return dict(output)  # type: ignore

    def get_recent_tasks_with_defaults(
        self,
        show_last_n_weeks: int,
    ) -> dict[str, str]:
        """
        Return the drop-down list of recent tasks with a flag to indicate
        default tasks.
        """
        latest_tasks = """
            select task, (indx = 0) as default_flag
            from task_detail_with_defaults
            where last_date_time >= datetime('now', :date_modifier)
               or indx = 0  /* Defaults */
            order by indx, task
        """
        output = read_sql(
            sql=latest_tasks,
            con=self.connection,
            params={"date_modifier": f"-{show_last_n_weeks * 7} days"},
        )

        return dict(output)  # type: ignore

    def get_details_for_task(self, task: str) -> list:
        """
        Return the list of recent detail for the task.

        TODO: Use memoisation/caching to avoid repeated queries to the DB.
        """
        details = self.connection.execute(
            """
            select detail
            from tracker
            where task = :task
            group by detail
            order by max(date_time) desc
            limit 10
            """,
            {"task": task},
        ).fetchall()
        return [detail[0] for detail in details]

    def post_event(self, entry: core.Entry) -> None:
        """
        The actions to perform after the event.
        """
        logger.debug("Doing database actions...")
        if DEBUG_MODE:
            return

        self.write_to_database(
            task=entry.task_name,
            detail=entry.detail,
            at_datetime=entry.date_time,
            interval=entry.interval,
        )

        # Only extract data on the hour -- consider making this more flexible
        if entry.date_time.minute == 0 and self.configuration.save_csv_copy:
            self.write_to_csv(filepath=self.configuration.csv_filepath)

    def write_to_database(
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
                insert into tracker(date_time, task, detail, interval)
                    values (:at_datetime, :task, :detail, :interval)
                """,
                {
                    "at_datetime": at_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "task": task,
                    "detail": detail,
                    "interval": interval,
                },
            )

    def write_to_csv(
        self, filepath: str, previous_days: int | None = None
    ) -> None:
        """
        Write the tracker history to a CSV file.

        By default, this will download the entire history. To limit this, set
        the number of days to limit this to with the `previous_days` parameter.
        """
        tracker_history = """
            select
                date_time,
                task,
                detail,
                interval
            from tracker
            where date_time >= date('now', :date_modifier)
            order by date_time
        """
        result = read_sql(
            sql=tracker_history,
            con=self.connection,
            params={"date_modifier": f"-{previous_days} days"},
        )
        headers = [("date_time", "task", "detail", "interval")]
        to_csv(
            data=headers + result,
            path=(
                pathlib.Path(filepath)
                / f"daily-tracker-{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
            ),
        )
