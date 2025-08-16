"""
Frontend for the tracker.

This is currently more of a POC, but will be improved over time.

TODO: Callbacks should be tied to the backend
"""
# ruff: noqa: S608

import datetime
import functools
from collections.abc import Callable

import pandas
import streamlit

from daily_tracker import utils
from daily_tracker.core.database import DatabaseConnector

CONN = DatabaseConnector(utils.DB)


def handle_exceptions(refresh: bool = False) -> Callable:
    """
    Decorator to handle function calls that raise an exception.
    """

    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def inner(*args, **kwargs) -> None:
            try:
                func(*args, **kwargs)
                if refresh:
                    pass
                    # streamlit.write("Refreshing in 3 seconds...")
                    # time.sleep(3)
                    # streamlit.experimental_rerun()
            except Exception as e:
                streamlit.write(
                    "Something went wrong! See the traceback below."
                )
                streamlit.write(e)

        return inner

    return wrapper


def execute(sql: str, parameters: dict | None = None) -> pandas.DataFrame:
    """
    Convert the result of a query to a dataframe.
    """
    result = CONN.execute(sql, parameters or {})

    return pandas.DataFrame(
        data=result.fetchall(),
        columns=[col_desc[0] for col_desc in result.description],
    )


def header_text() -> None:
    """
    Add the text at the top of the application.
    """
    streamlit.header("Daily Tracker :stopwatch:")
    streamlit.write(
        """
        Stuff to fiddle with the tracker backend.

        Should we have the "run" button here? Then the "run on open" option
        would make sense, and we can manage the application from here.
        """
    )
    streamlit.divider()


@handle_exceptions(refresh=True)
def copy_latest_callback(interval: int) -> None:
    """
    Copy the latest entry from the tracker.
    """
    CONN.connection.execute(
        """
        insert into tracker(date_time, task, detail, interval)
            select
                datetime(date_time, :interval_adjustment),
                task,
                detail,
                interval
            from tracker
            order by date_time desc
            limit 1
        """,
        {
            "interval_adjustment": f"+{interval} minutes",
        },
    )
    CONN.connection.commit()
    # streamlit.write("Entry inserted!")


def show_latest_entry() -> pandas.DataFrame:
    """
    Show the latest entry from the tracker.
    """
    streamlit.subheader("Latest entry")
    latest_entry = execute(
        """
        select *
        from tracker
        order by date_time desc
        limit 1
        """
    )
    latest_entry_transposed = latest_entry.transpose()

    frame, actions = streamlit.columns([2, 1])

    with frame:
        streamlit.markdown(
            latest_entry_transposed.to_html(header=False),
            unsafe_allow_html=True,
        )

    with actions:
        if streamlit.button("Make a copy (+ interval)"):
            copy_latest_callback(interval=15)
        if streamlit.button("Make a copy (recent)"):
            raise NotImplementedError

    streamlit.divider()
    return latest_entry


@handle_exceptions(refresh=True)
def insert_entry_callback(
    date_time: datetime.datetime,
    task: str,
    detail: str,
    interval: int,
) -> None:
    """
    Insert an entry into the tracker.
    """
    CONN.connection.execute(
        """
        insert into tracker(date_time, task, detail, interval)
        values (:date_time, :task, :detail, :interval)
        """,
        {
            "date_time": date_time.strftime("%Y-%m-%d %H:%M:%S"),
            "task": task,
            "detail": detail,
            "interval": interval,
        },
    )
    CONN.connection.commit()
    # streamlit.write("Entry inserted!")


def insert_entry(latest_entry: pandas.DataFrame) -> None:
    """
    Insert an entry into the tracker.
    """
    streamlit.subheader("Insert entry")

    entry = latest_entry.to_dict(orient="records")[0]
    date_and_time, details = streamlit.columns(2)

    with date_and_time:
        latest_datetime = datetime.datetime.fromisoformat(entry["date_time"])
        entry_date = streamlit.date_input("Date", value=latest_datetime)
        entry_time = streamlit.time_input("Time", value=latest_datetime)

    date_time = datetime.datetime.combine(entry_date, entry_time)

    with details:
        task = streamlit.text_input("Task", value=entry["task"])
        detail = streamlit.text_input("Detail", value=entry["detail"])
        # interval is taken from the configuration (?)

    if streamlit.button("Insert entry"):
        insert_entry_callback(date_time, task, detail, interval=15)

    streamlit.divider()


@handle_exceptions(refresh=True)
def update_row(date_time: str, changes: dict[str, str]) -> None:
    """
    Update a row in the tracker.
    """
    # We have to do a smidge of dynamic SQL here -- can we find a way to
    # use Metabase's [[ ]] syntax?

    conditions = ", ".join(f"{column} = :{column}" for column in changes)
    sql = f"""
        update tracker
        set {conditions}
        where date_time = :date_time
    """
    CONN.connection.execute(sql, {"date_time": date_time, **changes})
    CONN.connection.commit()


def save_changes_callback(edited_records: pandas.DataFrame) -> None:
    """
    Save changes to the tracker.
    """
    state = streamlit.session_state["tracker-editor"]
    for index, changes in state["edited_rows"].items():
        assert isinstance(changes, dict)  # noqa: S101
        # Get the PK from the Pandas index
        date_time = edited_records.loc[index, "date_time"]
        update_row(date_time, changes)


def edit_stuff() -> None:
    """
    Edit stuff.
    """
    streamlit.subheader("Edit stuff")

    filters, _ = streamlit.columns(2)

    with filters:
        from_date, to_date = streamlit.date_input(
            label="Date filter",
            value=[datetime.date.today(), datetime.date.today()],
        )

    records = execute(
        """
        select *
        from tracker
        where date_time between :from_date and :to_date
        """,
        {
            "from_date": from_date,
            "to_date": to_date,
        },
    )
    streamlit.data_editor(
        records,
        key="tracker-editor",
        disabled=["date_time"],
    )

    state = streamlit.session_state["tracker-editor"]
    edited_records: pandas.DataFrame = records.iloc[
        list(state["edited_rows"].keys())
    ]

    streamlit.write("Edited records:")
    if not edited_records.empty:
        streamlit.write(edited_records)

    # TODO: Extend this to be able to edit the date and time as well
    if streamlit.button(
        label="Save changes",
        disabled=edited_records.empty,
    ):
        save_changes_callback(edited_records)

    streamlit.divider()


@handle_exceptions(refresh=True)
def rename_something_callback(column: str, from_: str, to: str) -> None:
    """
    Rename something.
    """
    CONN.connection.execute(
        f"""
        update tracker
        set {column} = :to
        where {column} = :from_
        """,
        {
            "from_": from_,
            "to": to,
        },
    )
    CONN.connection.commit()


def rename_something() -> None:
    """
    Rename something.
    """
    streamlit.subheader("Rename something")

    select_option, filters = streamlit.columns(2)

    with select_option:
        option = streamlit.selectbox(
            "Which column do you want to rename values of?",
            ["task", "detail"],
        )

    with filters:
        from_date, to_date = streamlit.date_input(
            label="Date filter (selection only, all records are updated)",
            value=[
                datetime.date.today() - datetime.timedelta(days=7),
                datetime.date.today(),
            ],
        )

    to_rename, new_name = streamlit.columns(2)

    with to_rename:
        old_name = streamlit.selectbox(
            f"Old {option} name",
            options=execute(
                f"""
                select distinct {option}
                from tracker
                where date_time between :from_date and :to_date
                  and {option} is not null
                  and {option} != ''
                order by {option}
                """,
                {
                    "from_date": from_date,
                    "to_date": to_date,
                },
            ),
        )

    with new_name:
        new_name = streamlit.text_input(
            f"New {option} name",
            value=old_name,
        )

    if streamlit.button(f"Rename {option}", disabled=(old_name == new_name)):
        rename_something_callback(option, old_name, new_name)

    streamlit.divider()


def main() -> None:
    """
    The entry point into the application.
    """
    header_text()

    latest_entry = show_latest_entry()
    insert_entry(latest_entry)
    edit_stuff()
    rename_something()


if __name__ == "__main__":
    main()
