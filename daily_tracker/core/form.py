"""
The form for the pop-up box.

https://youtu.be/5qOnzF7RsNA
https://github.com/codefirstio/tkinter-data-entry
"""
import datetime
import logging
import textwrap
import tkinter as tk
import tkinter.ttk
from typing import Any

import PIL.Image
import PIL.ImageTk

import tracker_utils

ICON = tracker_utils.ROOT / "resources/clock-icon.png"
STYLE = {
    "font": ("Tahoma", 8),
}


def load_icon(filepath: str) -> PIL.ImageTk.PhotoImage | PIL.Image.Image:
    """
    Load an image to the ICO format so that it can be used as application icons.
    """
    return PIL.ImageTk.PhotoImage(PIL.Image.open(filepath))


class TrackerForm:
    """
    The pop-up box for the tracker.
    """

    def __init__(self, at_datetime: datetime.datetime, action_handler):
        """
        Create the form handler.
        """
        self.at_datetime = at_datetime
        self.action_handler = action_handler
        self.interval = self.action_handler.configuration.interval
        self._width = 350
        self._height = 150
        self._root: tk.Tk | None = None
        self.project_text_box: TextBox | None = None
        self.detail_text_box: TextBox | None = None
        # self._root.mainloop()
        # Add properties like `is_meeting` and `is_jira_ticket`?
        # self.generate_form()

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
    def date_time(self) -> str:
        """
        Return the pop-up datetime in the hh:mm format.
        """
        return self.at_datetime.strftime("%H:%M")

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
        logging.info(
            textwrap.dedent(
                f"""
                {30 * '-'}
                Project:  {self.task}
                Detail:   {self.detail}
                Interval: {self.interval}
                Datetime: {self.at_datetime.strftime('%Y-%m-%d %H:%M:%S')}
                {30 * '-'}
                """
            )
        )
        self.close_form()

    def on_project_change(self, *_) -> None:
        """
        When the value of the Project box changes, update the Detail box with
        the latest value from the Project.
        """
        details = self.action_handler.database_handler.get_details_for_task(
            self.task
        )
        self.detail_text_box.text_box["values"] = details
        self.detail_text_box.text_box.set(details[0] if details else "")

    def ok_shortcut(self, event: tk.Event) -> None:
        """
        Enable keyboard shortcut CTRL + ENTER to the OK button.

        https://youtu.be/ibf5cx221hk
        """
        if event.state == 12 and event.keysym == "Return":
            self.action_wrapper()

    def generate_form(self) -> None:
        """
        Generate the tracker pop-up form.
        """
        self._root = tk.Tk()
        self._root.geometry(f"{self._width}x{self._height}")
        self._root.eval("tk::PlaceWindow . center")  # Middle of screen
        self._root.title(
            f"Interval Tracker at {self.date_time} ({self.interval})"
        )
        self._root.wm_iconphoto(False, load_icon(ICON))

        text_box_frame_outer = tk.Frame(
            self._root,
            background="white",
        )
        text_box_frame_outer.pack(
            in_=self._root,
            fill="both",
            expand=tk.YES,
        )

        text_box_frame = tk.LabelFrame(
            self._root,
            text="Current Task Details",
            borderwidth=2,
            background="white",
            font=STYLE["font"],
        )
        text_box_frame.pack(
            # in_=self._root,
            in_=text_box_frame_outer,
            fill="both",
            expand=tk.YES,
            side=tk.TOP,
            padx=10,
            pady=10,
        )

        button_frame = tk.Frame(
            self._root,
            borderwidth=15,
        )
        button_frame.pack(
            in_=self._root,
            side=tk.BOTTOM,
            fill=tk.BOTH,
            expand=True,
        )

        defaults = self.action_handler.get_default_task_and_detail(
            self.at_datetime
        )
        options = self.action_handler.get_dropdown_options(
            use_jira_sprint=self.action_handler.configuration.use_jira_sprint
        )

        self.project_text_box = TextBox(
            parent=text_box_frame,
            label_text="Project",
            default=defaults[0],
            values=list(options),
        )
        self.detail_text_box = TextBox(
            parent=text_box_frame,
            label_text="Detail",
            default=defaults[1],
            values=self.action_handler.database_handler.get_details_for_task(
                defaults[0]
            ),
        )

        self.project_text_box.text_box.bind("<KeyPress>", self.ok_shortcut)
        self.detail_text_box.text_box.bind("<KeyPress>", self.ok_shortcut)

        # self.project_text_box.text_box.bind("<Key>", self.on_project_change)
        self.project_text_box.variable.trace("w", self.on_project_change)

        okay_button = tk.Button(
            self._root,
            height=2,
            width=20,
            borderwidth=3,
            text="OK",
            command=self.action_wrapper,
            font=STYLE["font"],
        )
        okay_button.pack(
            in_=button_frame,
            side=tk.LEFT,
        )
        # Could only get this to work by sticking the call inside a lambda
        okay_button.bind("<Return>", lambda _: self.action_wrapper())

        cancel_button = tk.Button(
            self._root,
            height=2,
            width=20,
            borderwidth=3,
            text="Cancel",
            command=self.close_form,
            font=STYLE["font"],
        )
        cancel_button.pack(
            in_=button_frame,
            side=tk.RIGHT,
        )
        # cancel_button.bind("<Return>", self.close_form)
        # Could only get this to work by sticking the call inside a lambda
        cancel_button.bind("<Return>", lambda _: self.close_form())

        self._root.mainloop()


class TextBox:
    """
    A text box with a label for the main form.
    """

    def __init__(
        self,
        parent: tk.Misc,
        label_text: str,
        default: Any,
        values: list[Any],
    ):
        """
        Set the text box properties and create the widget.
        """
        self.parent = parent
        self.label_text = label_text
        self.values = values
        self.frame = self._build(default)

        self.variable: str
        self.text_box: tk.ttk.Combobox

    def _build(self, default: Any) -> tk.Frame:
        """
        Build the text box and return it.
        """
        frame = tk.Frame(self.parent, background="white")
        inner = tk.Frame(self.parent, background="white")
        label = tk.Label(
            master=inner,
            height=1,
            width=8,
            borderwidth=2,
            text=self.label_text,
            justify="right",
            background="white",
            relief="flat",
            font=STYLE["font"],
        )

        text_box_value = tk.StringVar(inner)
        text_box_value.set(default)
        text_box = tk.ttk.Combobox(
            master=inner,
            textvariable=text_box_value,
            width=40,
            font=STYLE["font"],
            values=self.values,
        )
        # text_box.set(default)
        self.variable = text_box_value
        self.text_box = text_box

        label.pack(in_=inner, side=tk.LEFT)
        text_box.pack(in_=inner, side=tk.RIGHT)
        inner.pack(in_=frame, pady=4)
        frame.pack(in_=self.parent)

        return frame
