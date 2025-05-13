"""
The form for the pop-up box.

https://youtu.be/5qOnzF7RsNA
https://github.com/codefirstio/tkinter-data-entry
"""

from __future__ import annotations

import datetime
import logging
import textwrap
import tkinter
from tkinter import ttk

import ttkthemes

from daily_tracker import _actions, utils
from daily_tracker.core import database

logger = logging.getLogger("core")

ICON = utils.SRC / "resources/clock-icon.png"


class TrackerForm:
    """
    The pop-up box for the tracker.
    """

    at_datetime: datetime.datetime
    action_handler: _actions.ActionHandler
    interval: int
    _width: int
    _height: int
    _root: ttkthemes.ThemedTk
    project_text_box: TextBox
    detail_text_box: TextBox

    # Shouldn't this just be the first of the options?
    defaults: tuple[str, str]

    options: dict[str, str]
    # project_details: dict[str, list[str]]  # See `task_details` below

    def __init__(self, at_datetime: datetime.datetime, action_handler):
        """
        Create the form handler.
        """
        logger.debug(f"Creating the form for {at_datetime}.")
        self.at_datetime = at_datetime
        self.action_handler = action_handler
        self.interval = self.action_handler.configuration.interval
        self._width = 350
        self._height = 150
        self.defaults = self.action_handler.get_default_task_and_detail(
            at_datetime=self.at_datetime,
        )
        self.options = self.action_handler.get_dropdown_options(
            jira_filter=self.action_handler.configuration.jira_filter,
        )

    @property
    def task(self) -> str:
        """
        Return the current task value.
        """
        return self.project_text_box.text_box.get()

    @property
    def detail(self) -> str:
        """
        Return the current detail value.
        """
        return self.detail_text_box.text_box.get()

    @property
    def task_details(self) -> list[str]:
        """
        Return the current task's details.

        TODO: This should be given as an argument -- we don't want to have to
              talk to the database here (I think).
        """
        # fmt: off
        database_handler: database.Database = self.action_handler.inputs["database"]  # type: ignore
        return database_handler.get_details_for_task(self.task)
        # fmt: on

    @property
    def date_time(self) -> str:
        """
        Return the pop-up datetime in the hh:mm format.
        """
        return self.at_datetime.strftime("%H:%M")

    @property
    def title(self) -> str:
        """
        Return the title to use for the pop-up.
        """
        return f"Interval Tracker at {self.date_time} ({self.interval})"

    def close_form(self) -> None:
        """
        Close the form window.
        """
        self._root.destroy()
        # self._root.quit()
        # self._root.protocol("WM_DELETE_WINDOW", lambda: sys.exit())
        # self._root.protocol("WM_DELETE_WINDOW", self._root.destroy)

    def action_wrapper(self) -> None:
        """
        Wrap the action so that we can schedule the next event when it's called.
        """
        self.action_handler.ok_actions()
        logger.info(
            textwrap.dedent(
                f"""
                {30 * "-"}
                Project:  {self.task}
                Detail:   {self.detail}
                Interval: {self.interval}
                Datetime: {self.at_datetime.strftime("%Y-%m-%d %H:%M:%S")}
                {30 * "-"}
                """
            )
        )
        self.close_form()

    def on_project_change(self, *_) -> None:
        """
        When the value of the Project box changes, update the Detail box with
        the latest value from the Project.
        """
        details = self.task_details
        self.detail_text_box.text_box["values"] = details
        self.detail_text_box.text_box.set(details[0] if details else "")

    def ok_shortcut(self, event: tkinter.Event) -> None:
        """
        Enable keyboard shortcut CTRL + ENTER to the OK button.

        https://youtu.be/ibf5cx221hk
        """
        if event.state == 12 and event.keysym == "Return":  # noqa: PLR2004
            self.action_wrapper()

    def generate_form(self) -> None:
        """
        Generate the tracker pop-up form.
        """
        self._root = ttkthemes.ThemedTk(theme="arc")
        self._root.geometry(f"{self._width}x{self._height}")
        self._root.eval("tk::PlaceWindow . center")
        self._root.title(self.title)
        self._root.iconphoto(True, tkinter.PhotoImage(file=ICON))

        form_frame = ttk.Frame(self._root)
        form_frame.pack(expand=tkinter.YES, fill="both")

        text_box_frame = ttk.LabelFrame(
            form_frame,
            text="Current Task Details",
        )
        text_box_frame.pack(
            side="top",
            fill="both",
            expand=tkinter.YES,
            padx=10,
            pady=10,
        )

        button_frame = ttk.Frame(form_frame)
        button_frame.pack(
            side="bottom",
            fill="both",
            expand=tkinter.TRUE,
            padx=10,
            pady=(0, 10),
        )

        self.set_text_boxes(text_box_frame)
        self.set_buttons(button_frame)

        self._root.mainloop()

    def set_text_boxes(self, text_box_frame: ttk.LabelFrame) -> None:
        """
        Set the text boxes for the form.
        """
        self.project_text_box = TextBox(
            parent=text_box_frame,
            label_text="Project",
            default=self.defaults[0],
            values=list(self.options),
        )
        self.detail_text_box = TextBox(
            parent=text_box_frame,
            label_text="Detail",
            default=self.defaults[1],
            values=self.task_details,
        )

        self.project_text_box.text_box.bind("<KeyPress>", self.ok_shortcut)
        self.detail_text_box.text_box.bind("<KeyPress>", self.ok_shortcut)

        # self.project_text_box.text_box.bind("<Key>", self.on_project_change)
        self.project_text_box.variable.trace("w", self.on_project_change)

    def set_buttons(self, button_frame: ttk.Frame) -> None:
        """
        Set the buttons for the form.
        """
        okay_button = ttk.Button(
            button_frame,
            text="OK",
            command=self.action_wrapper,
        )
        okay_button.pack(side="left", expand=tkinter.TRUE, padx=10)

        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.close_form,
        )
        cancel_button.pack(side="right", expand=tkinter.TRUE, padx=10)

        # Could only get these to work by sticking the call inside a lambda
        okay_button.bind("<Return>", lambda _: self.action_wrapper())
        cancel_button.bind("<Return>", lambda _: self.close_form())


class TextBox:
    """
    A text box with a label for the main form.
    """

    parent: ttk.LabelFrame
    label_text: str
    values: list[str]
    frame: ttk.Frame
    variable: tkinter.StringVar
    text_box: ttk.Combobox

    def __init__(
        self,
        parent: ttk.LabelFrame,
        label_text: str,
        default: str,
        values: list[str],
    ):
        """
        Set the text box properties and create the widget.
        """
        self.parent = parent
        self.label_text = label_text
        self.values = values
        self.frame = self._build(default)

    def _build(self, default: str) -> ttk.Frame:
        """
        Build the text box and return it.
        """
        frame = ttk.Frame(self.parent)
        frame.pack(ipady=4)

        label = ttk.Label(
            frame,
            text=self.label_text,
            width=8,
            anchor="e",
        )

        text_box_value = tkinter.StringVar(frame)
        text_box_value.set(default)
        text_box = ttk.Combobox(
            frame,
            textvariable=text_box_value,
            width=40,
            values=self.values,
        )

        self.variable = text_box_value
        self.text_box = text_box

        label.pack(side="left", padx=2)
        text_box.pack(side="right", padx=2)

        return frame
