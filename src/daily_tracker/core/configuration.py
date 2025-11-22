"""
The configuration options of the tracker.

TODO: This is mastered in the ``configuration.yaml`` file, so do we need
    this class? Or should we just use ``yaml2pyclass``?

    https://github.com/a-nau/yaml2pyclass

TODO: Inherit types from the JSON schema validator file?
"""

from __future__ import annotations

import collections
import pathlib
from typing import Any

import yaml

from daily_tracker import utils

# TODO: Take the default values from the JSON schema validator file
DEFAULT_CONFIG = utils.DAILY_TRACKER / "resources/configuration.yaml"


class Configuration:
    """
    The configuration of the tracker.

    Extremely simple implementation -- will expand this in the future to be
    more dynamic. Or just leave as a simple dict?

    The docstrings should be taken from the ``description`` property.
    """

    def __init__(self, configuration: dict) -> None:
        self.configuration = configuration
        self.options = self.configuration["tracker"]["options"]

    @classmethod
    def _from_default(cls, filepath: str = DEFAULT_CONFIG) -> Configuration:
        """
        Read the configuration YAML files into a Configuration object.

        Uses two different configuration files: a default one that build with
        the application, and one for the user to edit.

        TODO: Include the API tokens/keys/secrets in the config file (#5)
        """
        with open(filepath) as f_custom, open(DEFAULT_CONFIG) as f_base:
            config = yaml.load(f_custom.read(), yaml.Loader)  # noqa: S506

            config["tracker"]["options"] = collections.ChainMap(
                config["tracker"]["options"],
                yaml.load(f_base.read(), yaml.Loader)["tracker"]["options"],  # noqa: S506
            )

            return Configuration(config)

    @classmethod
    def from_default(cls) -> Configuration:
        """
        Read the ``configuration.yaml`` into a Configuration object.
        """
        with open(DEFAULT_CONFIG) as f:
            return Configuration(yaml.load(f.read(), yaml.Loader))  # noqa: S506

    def _get_option_value(self, option: str, default: Any) -> Any:
        return self.options.get(option, default)

    @property
    def interval(self) -> int:
        return self._get_option_value("interval", False)

    @property
    def keep_awake(self) -> bool:
        return self._get_option_value("keep-awake", False)

    @property
    def run_on_startup(self) -> bool:
        return self._get_option_value("run-on-startup", False)

    @property
    def show_last_n_weeks(self) -> int:
        return self._get_option_value("show-last-n-weeks", 2)

    @property
    def appointment_category_exclusions(self) -> list[str]:
        return self._get_option_value("appointment-category-exclusions", [])

    @property
    def linked_calendar(self) -> str:
        return self._get_option_value("linked-calendar", None)

    @property
    def jira_filter(self) -> str:
        return self._get_option_value("jira-filter", None)

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
    def monday_filter(self) -> str:
        return self._get_option_value("monday-filter", None)
