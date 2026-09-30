"""
Connect to and read from a Jira project using its REST API:
    * https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/

This only supports the Cloud version of Jira, not the Server version.

Note that:
    * The KEY should be your email address for your Atlassian account
    * The SECRET should be a token that you generate for your Atlassian account
See more at:
    * https://id.atlassian.com/manage-profile/security/api-tokens

TODO: This should be updated to pick up the API implementation from the Jira
 swagger documentation, though it's unclear what the best source is for it. See:
    * https://jira.atlassian.com/browse/JRASERVER-68539
"""

import datetime
import http
import json
import logging
import os
import re

import requests
import requests.auth

from daily_tracker import core

logger = logging.getLogger("integrations")

TIMEOUT_SECONDS = 20
JIRA_CREDENTIALS = {
    "domain": os.getenv("JIRA_DOMAIN"),
    "key": os.getenv("JIRA_KEY"),
    "secret": os.getenv("JIRA_SECRET"),
}


class JiraConnector:
    """
    Naive implementation of a connector to Jira via its REST API.

    This just exposes the Jira endpoints in a Pythonic way, but doesn't add
    any layers on top of this.
    """

    def __init__(self, domain: str, key: str, secret: str) -> None:
        self._base_url = f"https://{domain}.atlassian.net/rest/api/3/"
        self.auth_basic = requests.auth.HTTPBasicAuth(key, secret)

    @property
    def request_headers(self) -> dict:
        """
        Expose the default headers in a dictionary.
        """

        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_projects_paginated(
        self,
        max_results: int = 50,
    ) -> requests.Response:
        """
        Call the "Get projects paginated" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-projects/#api-rest-api-3-project-search-get
        """

        endpoint = "project/search"
        return requests.get(
            url=self._base_url + endpoint,
            headers=self.request_headers,
            auth=self.auth_basic,
            params={"maxResults": max_results},
            timeout=TIMEOUT_SECONDS,
        )

    def get_issue(self, issue_key: str) -> requests.Response:
        """
        Call the "Get issue" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get
        """

        endpoint = f"issue/{issue_key}"
        return requests.get(
            url=self._base_url + endpoint,
            headers=self.request_headers,
            auth=self.auth_basic,
            data={},
            timeout=TIMEOUT_SECONDS,
        )

    def search_for_issues_using_jql(
        self,
        jql: str,
        fields: list[str],
        next_page_token: str = "",
        max_results: int = 50,
    ) -> requests.Response:
        """
        Call the "Search for issues using JQL enhanced search (GET)" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-get
        """

        endpoint = "search/jql"
        params = {
            "jql": jql,
            "fields": fields,
            "maxResults": max_results,
        }
        if next_page_token:
            params["nextPageToken"] = next_page_token

        return requests.get(
            url=self._base_url + endpoint,
            headers=self.request_headers,
            auth=self.auth_basic,
            params=params,
            timeout=TIMEOUT_SECONDS,
        )

    def get_project_components(self, project_id: str) -> requests.Response:
        """
        Call the "Get project components" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-components/#api-rest-api-3-project-projectidorkey-components-get
        """

        endpoint = f"project/{project_id}/components"
        return requests.get(
            url=self._base_url + endpoint,
            headers=self.request_headers,
            auth=self.auth_basic,
            data={},
            timeout=TIMEOUT_SECONDS,
        )

    def get_project_roles(self) -> requests.Response:
        """
        Call the "Get project roles" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-roles
        """

        endpoint = "role"
        return requests.get(
            url=self._base_url + endpoint,
            headers=self.request_headers,
            auth=self.auth_basic,
            data={},
            timeout=TIMEOUT_SECONDS,
        )

    def add_worklog(
        self,
        issue_key: str,
        detail: str,
        at_datetime: datetime.datetime,
        interval: int,
    ) -> requests.Response | None:
        """
        Call the "Add worklog" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-worklogs/#api-rest-api-3-issue-issueidorkey-worklog-post

        :param issue_key: The key of the issue to add the worklog to.
        :param detail: The details of the worklog to add.
        :param at_datetime: The timestamp corresponding to the start of the
            worklog. Note that this must be a string in the format
            %Y-%m-%dT%H:%M:%S.000+0000
        :param interval: The number of minutes that this worklog corresponds to.

        TODO: Change this so that it updates the previous worklog if multiple
            work logs are added in succession.
        """

        endpoint = f"issue/{issue_key}/worklog"
        payload = json.dumps(
            {
                "timeSpentSeconds": interval * 60,
                "comment": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "text": detail,
                                    "type": "text",
                                }
                            ],
                        }
                    ],
                },
                # TODO: Make this timezone-aware
                "started": f"{at_datetime.strftime('%Y-%m-%dT%H:%M:%S')}.000+0000",
            }
        )

        try:
            return requests.post(
                url=self._base_url + endpoint,
                headers=self.request_headers,
                auth=self.auth_basic,
                data=payload,
                timeout=TIMEOUT_SECONDS,
            )
        except Exception as e:
            logger.debug(f"Could not add worklog: {e}")

    def create_issue(
        self,
        project_id: str,
        summary: str,
        description: str,
    ) -> requests.Response:
        """
        Call the "Create issue" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post
        """

        endpoint = "issue"
        payload = json.dumps(
            {
                "update": {},
                "fields": {
                    "summary": summary,
                    "issuetype": {"id": "10001"},  # Task
                    "project": {"id": project_id},
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "text": description,
                                        "type": "text",
                                    }
                                ],
                            }
                        ],
                    },
                    "labels": [],
                    "duedate": None,
                },
            }
        )

        return requests.post(
            url=self._base_url + endpoint,
            headers=self.request_headers,
            auth=self.auth_basic,
            data=payload,
            timeout=TIMEOUT_SECONDS,
        )


class Jira(core.Input, core.Output):
    """
    The Jira handler.

    This bridges the input and output objects with the REST API connector
    object to implement the input and output actions.
    """

    def __init__(
        self,
        configuration: core.Configuration,
        debug_mode: bool = False,
    ) -> None:
        self.connector = JiraConnector(**JIRA_CREDENTIALS)
        self.project_key_pattern = re.compile(r"^[A-Z]\w{1,9}-\d+")
        self.configuration = configuration
        self.debug_mode = debug_mode

    def debug(self) -> tuple[int, str]:
        return 1, "Jira connection debugger not implemented yet"

    def on_event(self, date_time: datetime.datetime) -> list[core.Task]:
        """
        The actions to perform before the event.
        """

        if self.configuration.jira_filter:
            return [
                core.Task(task_name=ticket)
                for ticket in self.get_tickets_in_sprint()
            ]

        return []

    def get_tickets_in_sprint(self) -> list[str]:
        """
        Get the list of tickets in the active sprint for the current user.
        """

        def get_batch_of_tickets(next_page_token: str = "") -> dict:
            """
            Inner function to loop over until all tickets have been retrieved.
            """

            try:
                return json.loads(
                    self.connector.search_for_issues_using_jql(
                        jql=self.configuration.jira_filter,
                        fields=["summary", "duedate", "assignee"],
                        next_page_token=next_page_token,
                    ).text
                )
            except (
                requests.exceptions.JSONDecodeError,  # Usually because Jira is down
                requests.exceptions.ProxyError,  # Sometimes pops up behind a proxy
            ):
                return {"total": 1_000, "issues": []}

        results = []
        next_token, is_last = "", False
        total = 999
        retries = 0
        max_retries = 5
        while len(results) < total and retries < max_retries and not is_last:
            response = get_batch_of_tickets(next_page_token=next_token)
            if "errorMessages" in response:
                error_message = " ".join(response["errorMessages"])
                logger.warning(
                    f"Could not get tickets in sprint: {error_message}"
                )
                return []

            next_token = response["nextPageToken"]
            is_last = response["isLast"]
            results += [
                f"{issue['key']} {issue['fields']['summary']}"
                for issue in response["issues"]
            ]
            retries += 1

        return results

    def post_event(self, entry: core.Entry) -> None:
        """
        The actions to perform after the event.
        """

        logger.debug("Doing Jira actions...")
        if self.debug_mode:
            return

        if self.configuration.post_to_jira:
            self.post_log_to_jira(
                task=entry.task_name,
                detail=entry.detail,
                at_datetime=entry.date_time,
                interval=entry.interval,
            )

    def post_log_to_jira(
        self,
        task: str,
        detail: str,
        at_datetime: datetime.datetime,
        interval: int,
    ) -> None:
        """
        Post the task, detail, and time to the corresponding ticket's worklog.
        """

        logger.debug("Posting log to Jira...")
        issue_key = re.search(self.project_key_pattern, task)
        if issue_key is None:
            logger.debug(f"Could not find {self.project_key_pattern} in {task}")
            return

        logger.debug(f"Posting work log to {issue_key[0]}")
        response = self.connector.add_worklog(
            issue_key=issue_key[0],
            detail=detail,
            at_datetime=at_datetime,
            interval=interval,
        )
        if response is None:
            logger.debug("Could not post work log, see above")
        elif response.status_code != http.HTTPStatus.CREATED:
            logger.debug(f"Response code: {response.status_code}")
            logger.debug(f"Could not post work log: {response.text}")


if __name__ == "__main__":
    config_ = core.Configuration.from_default()

    def pp(response: requests.Response) -> None:
        print(json.dumps(response.json(), indent=2))
        print()

    # jira_conn = JiraConnector(**JIRA_CREDENTIALS)
    # pp(jira_conn.get_projects_paginated())
    # pp(jira_conn.get_issue("DPP-10703"))
    # pp(
    #     jira_conn.search_for_issues_using_jql(
    #         # jql=config_.jira_filter,
    #         jql="sprint IN 'Sprint 195'",
    #         fields=["summary", "duedate", "assignee"],
    #     )
    # )
    #
    # jira_: Jira = Jira(configuration=config_)
    # tickets = jira_.get_tickets_in_sprint()
    # print(f"found {len(tickets)} tickets:")
    # for ticket in tickets:
    #     print("\t", ticket)
