"""
Connect to and read from a Monday.com project using its GraphQL API:
    - https://developer.monday.com/api-reference/docs/basics

Note that:
    - The API_TOKEN should be generated from your Monday.com account
See more at:
    - https://developer.monday.com/api-reference/docs/authentication
"""

from __future__ import annotations

import collections
import datetime
import logging
import os
from typing import Any

import dotenv
import requests

from daily_tracker import core, utils

dotenv.load_dotenv(dotenv_path=utils.DAILY_TRACKER.parent.parent / ".env")
logger = logging.getLogger("integrations")

BASE_URL = "https://api.monday.com/v2/"
TIMEOUT_SECONDS = 60
SIERRA_SQUAD_WORKSPACE_ID = 2462089
WEEKLY_CAPACITY_PLANNING_DASHBOARD_ID = 18825905
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

    def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> requests.Response:
        """
        Send a GraphQL query to the API and return the response.
        """

        return requests.post(
            url=BASE_URL,
            headers=self.request_headers,
            timeout=TIMEOUT_SECONDS,
            json={
                "query": query,
                "variables": variables or {},
            },
        )

    def get_me(self) -> requests.Response:
        """
        Retrieve information about the current user.

        https://developer.monday.com/api-reference/reference/me
        """

        return self.query(
            """
            query {
                me {
                    id
                    name
                }
            }
            """
        )

    def get_favourites(self) -> requests.Response:
        """
        Retrieve information about the current user's favourites.

        https://developer.monday.com/api-reference/reference/favorites
        """

        return self.query(
            """
            query {
                favorites {
                    accountId
                    createdAt
                    folderId
                    id
                    object {
                        id
                        type
                    }
                    position
                    updatedAt
                }
            }
            """
        )

    def get_workspaces(
        self,
        workspace_ids: int | list[int],
    ) -> requests.Response:
        """
        Retrieve information about the specified workspace.

        https://developer.monday.com/api-reference/reference/workspaces
        """

        return self.query(
            query="""
                query($workspace_ids: [ID!]) {
                    workspaces(ids: $workspace_ids) {
                        id
                        name
                        description
                        kind
                    }
                }
            """,
            variables={
                "workspace_ids": workspace_ids,
            },
        )

    def get_all_boards(self) -> requests.Response:
        """
        Retrieve information about the specified workspace.

        https://developer.monday.com/api-reference/reference/boards
        """

        return self.query(
            """
            query {
                boards(limit: 500) {
                    id
                    name
                    description
                    board_kind
                }
            }
            """
        )

    def get_boards(
        self,
        board_ids: int | list[int] | None = None,
        workspace_ids: int | list[int] | None = None,
    ) -> requests.Response:
        """
        Retrieve information about the specified workspace.

        https://developer.monday.com/api-reference/reference/boards
        """

        return self.query(
            query="""
                query($board_ids: [ID!], $workspace_ids: [ID!]) {
                    boards(
                        ids: $board_ids
                        workspace_ids: $workspace_ids
                        limit: 500
                    ) {
                        id
                        name
                        description
                        board_kind
                        columns {
                            id
                            title
                            type
                        }
                    }
                }
            """,
            variables={
                "board_ids": board_ids,
                "workspace_ids": workspace_ids,
            },
        )


class Monday(core.Input):
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

        monday_items = self.connector.query(self.configuration.monday_filter)
        tasks = collections.defaultdict(list)
        for list_of_board_results in monday_items.json()["data"].values():
            for board_result in list_of_board_results:
                for item in board_result["items_page"]["items"]:
                    task_name = item["parent_item"]["name"]
                    tasks[task_name].append(item["name"])

        return sorted(
            [core.Task(task, details) for task, details in tasks.items()]
        )


# if __name__ == "__main__":
#     import json
#     config_ = core.Configuration.from_default()
#     monday = MondayConnector(**MONDAY_CREDENTIALS)
#     def pp(response: requests.Response) -> None:
#         print(json.dumps(response.json(), indent=2))
#         print()
#     pp(monday.get_me())
#     pp(monday.get_favourites())
#     pp(monday.get_workspaces(SIERRA_SQUAD_WORKSPACE_ID))
#     pp(monday.get_all_boards())
#     pp(monday.get_boards(workspace_ids=SIERRA_SQUAD_WORKSPACE_ID))
#     pp(monday.get_boards(board_ids=[3137038078]))
