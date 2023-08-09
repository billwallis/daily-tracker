"""
Maintain the backend SQLite database.
"""
import sqlite3
from typing import Iterable

import daily_tracker.utils


class DatabaseConnector:
    """
    Connects to a SQLite database.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.connection = sqlite3.connect(self.filepath, timeout=15)
        self._create_backend()

    def execute(self, sql: str, parameters: Iterable = None) -> sqlite3.Cursor:
        """
        Shortcut to the execute method on the SQLite connection object.
        """
        return self.connection.execute(sql, parameters)  # noqa

    def run_query_from_file(self, filepath: str) -> sqlite3.Cursor:
        """
        Open a file and execute the query inside it.
        """
        with open(filepath, "r") as f:
            return self.connection.executescript(f.read())

    def _create_backend(self) -> None:
        """
        Create the backend if it doesn't already exist.
        """
        if not(
            self.connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'tracker'
                """
            ).fetchone()
        ):
            self.run_query_from_file(daily_tracker.utils.ROOT / "core" / "database" / "create.sql")

    def truncate_table(self, table_name: str) -> None:
        """
        Truncate a table if it exists.
        """
        if (
            self.connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = :table_name
                """,
                {"table_name": table_name}
            ).fetchone()
        ):
            self.connection.execute(
                f"""
                DELETE FROM {table_name} WHERE 1=1
                """
            )
