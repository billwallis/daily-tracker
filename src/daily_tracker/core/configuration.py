"""
The configuration options of the tracker.
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List

import yaml


FILE_PATH = "daily_tracker/core/configuration.yaml"


def get_configuration(filepath: str = FILE_PATH) -> Configuration:
    """
    Read the ``configuration.yaml`` into a Configuration object.
    """
    with open(filepath, "r") as f:
        return Configuration(yaml.load(f.read(), yaml.Loader))


class Configuration:
    """
    The configuration of the tracker.

    Extremely simple implementation -- will expand this in the future to be more
    dynamic. Or just leave as a simple dict?

    The docstrings should be taken from the ``description`` property.
    """
    def __init__(self, configuration: dict):
        self.configuration = configuration
        self.options = self.configuration["tracker"]["options"]

    def _get_option_value(self, option: str, default: Any) -> Any:
        return self.options.get(option, {}).get("value", default)

    @property
    def interval(self) -> int:
        return self._get_option_value("interval", False)

    @property
    def run_on_startup(self) -> bool:
        return self._get_option_value("run-on-startup", False)

    @property
    def show_last_n_weeks(self) -> int:
        return self._get_option_value("show-last-n-weeks", 2)

    @property
    def use_calendar_appointments(self) -> bool:
        return self._get_option_value("use-calendar-appointments", False)

    @property
    def appointment_category_exclusions(self) -> List[str]:
        return self._get_option_value("appointment-category-exclusions", None)

    @property
    def linked_calendar(self) -> str:
        return self._get_option_value("linked-calendar", None)

    @property
    def use_jira_sprint(self) -> bool:
        return self._get_option_value("use-jira-sprint", False)

    @property
    def post_to_slack(self) -> bool:
        return self._get_option_value("post-to-slack", False)

    @property
    def post_to_jira(self) -> bool:
        return self._get_option_value("post-to-jira", False)

    @property
    def save_csv_copy(self) -> bool:
        return self._get_option_value("save-csv-copy", False)

    @property
    def csv_filepath(self) -> str:
        return self._get_option_value("csv-filepath", str(pathlib.Path.home()))

    @property
    def appointment_exceptions(self) -> Dict[str, str]:
        return {
            item["name"]: (item["task"], item["detail"])
            for item in self.configuration["tracker"]["options"]["appointment-exceptions"]["value"]
        }
