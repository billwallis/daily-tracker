"""
Create the backend and configuration files the first time the
application is deployed.
"""

import pathlib

from daily_tracker import core, utils
from daily_tracker.core import database


def create_env() -> None:
    """
    Create the .env file.

    This should be deprecated and the values should be saved in the config
    file instead.
    """
    filepath = ".env"
    if pathlib.Path(filepath).exists():
        return

    with open(filepath, "w+") as f:
        keys = ["JIRA_URL", "JIRA_KEY", "JIRA_SECRET", "SLACK_URL"]
        f.write("\n".join([f"{key}=" for key in keys]))


def main() -> None:
    """
    Create the config files and database, then load existing data into the
    database.
    """
    create_env()
    db_handler = database.Database(
        database_filepath=utils.DB,
        configuration=core.Configuration.from_default(),
    )
    db_handler.import_history(filepath=utils.SRC / "tracker.csv")


if __name__ == "__main__":
    main()
