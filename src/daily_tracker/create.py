"""
Create the backend and configuration files the first time the application is
deployed.
"""
import pathlib

import daily_tracker.core
import daily_tracker.utils


def create_env() -> None:
    """
    Create the .env file.

    This should be depreciated and the values should be saved in the config file
    instead.
    """
    filepath = ".env"
    if pathlib.Path(filepath).exists():
        return None

    with open(filepath, "w+") as f:
        keys = ["JIRA_URL", "JIRA_KEY", "JIRA_SECRET", "SLACK_URL"]
        f.write("\n".join([f"{key}=" for key in keys]))


def main() -> None:
    """
    Create the config files and database, then load existing data into the
    database.
    """
    create_env()
    db_handler = daily_tracker.core.DatabaseHandler(
        database_filepath=daily_tracker.utils.ROOT / "tracker.db",
        configuration=daily_tracker.core.Configuration(),
    )
    db_handler.import_history(filepath=daily_tracker.utils.ROOT / "tracker.csv")


if __name__ == "__main__":
    main()
