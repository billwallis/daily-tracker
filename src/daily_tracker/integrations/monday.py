"""
Connect to and read from a Monday.com project using its GraphQL API:
    - https://developer.monday.com/api-reference/docs/basics

Note that:
    - The API_TOKEN should be generated from your Monday.com account
See more at:
    - https://developer.monday.com/api-reference/docs/authentication
"""

import datetime
import json
import logging
import os
from typing import Any

import dotenv
import requests

from daily_tracker import core, utils

dotenv.load_dotenv(dotenv_path=utils.DAILY_TRACKER.parent.parent / ".env")
logger = logging.getLogger("integrations")

BASE_URL = "https://api.monday.com/v2/"
TEN_SECONDS = 10
MONDAY_CREDENTIALS = {
    "api_token": os.getenv("MONDAY_API_TOKEN"),
}


class MondayConnector:
    """
    Naive implementation of a connector to Monday.com via its GraphQL API.
    """

    def __init__(self, api_token: str) -> None:
        self._api_token = api_token

    @property
    def request_headers(self) -> dict:
        """
        Expose the default headers in a dictionary.
        """

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self._api_token,
        }

    def query(self, query: Any) -> requests.Response:
        """
        Send a GraphQL query to the API and return the response.
        """

        return requests.post(
            url=BASE_URL,
            headers=self.request_headers,
            timeout=TEN_SECONDS,
            data=json.dumps({"query": query}),
        )

    def get_me(self) -> requests.Response:
        """
        Retrieve information about the current user.

        https://developer.monday.com/api-reference/reference/me
        """

        # TODO: Switch to use my New Relic pattern
        return self.query("query { me { id name } }")


class Monday(core.Input, core.Output):
    """
    The Monday.com handler.

    This bridges the input and output objects with the API connector to
    implement the input and output actions.
    """

    def __init__(
        self,
        configuration: core.Configuration,
        debug_mode: bool = False,
    ) -> None:
        self.connector = MondayConnector(**MONDAY_CREDENTIALS)
        self.configuration = configuration
        self.debug_mode = debug_mode

    def on_event(self, date_time: datetime.datetime) -> list[core.Task]:
        """
        The actions to perform before the event.
        """

        logger.debug("Doing Monday.com actions...")
        return []

    def post_event(self, entry: core.Entry) -> None:
        """
        The actions to perform after the event.
        """

        logger.debug("Doing Monday.com actions...")


if __name__ == "__main__":
    monday = MondayConnector(**MONDAY_CREDENTIALS)
    response = monday.get_me()
    print(response.json())
