"""
Connect to and read from GitHub using its REST API:
    - https://docs.github.com/en/rest?apiVersion=2022-11-28

Note that:
    - The GITHUB_TOKEN should be generated from your GitHub account

See more at:
    - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
"""

from __future__ import annotations

import datetime
import logging
import os

import cachetools
import dotenv
import requests

from daily_tracker import core, utils

dotenv.load_dotenv(dotenv_path=utils.DAILY_TRACKER.parent.parent / ".env")
logger = logging.getLogger("integrations")

BASE_URL = "https://api.github.com/"
TIMEOUT_SECONDS = 60
GITHUB_CREDENTIALS = {
    "api_token": os.getenv("GITHUB_TOKEN"),
}


class GitHubConnector:
    """
    Naive implementation of a connector to GitHub via its REST API.
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
            "Authorization": f"Bearer {self._api_token}",
        }

    def search_issues(self, search: str) -> requests.Response:
        """
        Search issues for the given search
        """

        # `params` is encoding the search incorrectly?!
        endpoint = f"search/issues?q={search}"

        return requests.get(
            url=BASE_URL + endpoint,
            headers=self.request_headers,
            timeout=TIMEOUT_SECONDS,
        )


class GitHub(core.Input):
    """
    The GitHub handler.

    This bridges the input and output objects with the API connector to
    implement the input and output actions.
    """

    def __init__(
        self,
        configuration: core.Configuration,
        debug_mode: bool = False,
    ) -> None:
        self.connector = GitHubConnector(**GITHUB_CREDENTIALS)
        self.configuration = configuration
        self.debug_mode = debug_mode

    @cachetools.cached(cache=cachetools.TTLCache(maxsize=1, ttl=60))
    def _on_event(self) -> list[core.Task]:
        """
        Cachable ``on_event`` action.
        """

        search_results = self.connector.search_issues(
            self.configuration.github_issues_search
        )
        details = set()
        for item in search_results.json()["items"]:
            details.add(
                ""
                + item["repository_url"].removeprefix(
                    "https://api.github.com/repos/"
                )
                + "#"
                + str(item["number"])
                + " "
                + item["title"]
            )

        return sorted(
            # TODO: Don't hardcode "Peer Review"
            [core.Task("Peer Review", detail) for detail in details]
        )

    def on_event(self, date_time: datetime.datetime) -> list[core.Task]:
        """
        The actions to perform before the event.
        """

        return self._on_event()


if __name__ == "__main__":
    import json

    config_ = core.Configuration.from_default()
    ghc = GitHubConnector(**GITHUB_CREDENTIALS)

    def pp(response: requests.Response) -> None:
        print(json.dumps(response.json(), indent=2))
        print()

    # pp(ghc.search_issues(config_.github_issues_search))

    gh = GitHub(config_)
    [print(d) for d in gh.on_event(datetime.datetime.now())]
