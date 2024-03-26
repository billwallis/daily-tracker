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

import base64
import datetime
import json
import logging
import os
import re

import dotenv
import requests

import core
import utils

# TODO: Can we correctly move this to the main file? (Simply moving it didn't work)
dotenv.load_dotenv(dotenv_path=utils.SRC.parent / ".env")
logger = logging.getLogger("integrations")

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

    def __init__(self, domain: str, key: str, secret: str):
        self._base_url = f"https://{domain}.atlassian.net/rest/api/3/"
        self._api_key = key
        self._api_secret = secret

    @property
    def auth_basic(self) -> str:
        """
        Encode the key and secret using Basic Authentication.

        See more at the Atlassian documentation:
            https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/#supply-basic-auth-headers
        """
        return "Basic " + base64.b64encode(f"{self._api_key}:{self._api_secret}".encode()).decode()

    @property
    def request_headers(self) -> dict:
        """
        Expose the default headers in a dictionary.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.auth_basic,
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
        return requests.request(
            method="GET",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            params={"maxResults": max_results},
        )

    def get_issue(self, issue_key: str) -> requests.Response:
        """
        Call the "Get issue" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-issueidorkey-get
        """
        endpoint = f"issue/{issue_key}"
        return requests.request(
            method="GET",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            data={},
        )

    def search_for_issues_using_jql(
        self,
        jql: str,
        fields: list[str],
        start_at: int = 0,
        max_results: int = 50,
    ) -> requests.Response:
        """
        Call the "Search for issues using JQL (GET)" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
        """
        endpoint = "search"
        params = {
            "jql": jql,
            "fields": fields,
            "startAt": start_at,
            "maxResults": max_results,
        }
        return requests.request(
            method="GET",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            params=params,
        )

    def get_project_components(self, project_id: str) -> requests.Response:
        """
        Call the "Get project components" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-components/#api-rest-api-3-project-projectidorkey-components-get
        """
        endpoint = f"project/{project_id}/components"
        return requests.request(
            method="GET",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            data={},
        )

    def get_project_roles(self) -> requests.Response:
        """
        Call the "Get project roles" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-project-roles
        """
        endpoint = "role"
        return requests.request(
            method="GET",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            data={},
        )

    def add_worklog(
        self,
        issue_key: str,
        detail: str,
        at_datetime: datetime.datetime,
        interval: int,
    ) -> requests.Response:
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
            return requests.request(
                method="POST",
                url=self._base_url + endpoint,
                headers=self.request_headers,
                data=payload,
            )
        except Exception as e:  # noqa
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
        return requests.request(
            method="POST",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            data=payload,
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
    ):
        self.connector = JiraConnector(**JIRA_CREDENTIALS)
        self.project_key_pattern = re.compile(r"^[A-Z]\w{1,9}-\d+")
        self.configuration = configuration
        self.debug_mode = debug_mode

    def on_event(self, date_time: datetime.datetime) -> list[core.Task]:
        """
        The actions to perform before the event.
        """
        if self.configuration.use_jira_sprint:
            return [core.Task(task_name=ticket) for ticket in self.get_tickets_in_sprint()]

        return []

    def get_tickets_in_sprint(self, project_key: str = None) -> list[str]:
        """
        Get the list of tickets in the active sprint for the current user.
        """
        fields = ["summary", "duedate", "assignee"]
        jql = " AND ".join(
            item
            for item in [
                f"project = {project_key}" if project_key else None,
                "sprint IN openSprints()",
                "assignee = currentUser()",
            ]
            if item is not None
        )

        def get_batch_of_tickets(start_at: int) -> dict:
            """
            Inner function to loop over until all tickets have been retrieved.
            """
            try:
                return json.loads(
                    self.connector.search_for_issues_using_jql(
                        jql=jql,
                        fields=fields,
                        start_at=start_at,
                    ).text
                )
            except (
                requests.exceptions.JSONDecodeError,  # Usually because Jira is down
                requests.exceptions.ProxyError,  # Sometimes pops up behind a proxy
            ):
                return {"total": 1_000, "issues": []}

        results = []
        total = 999
        retries = 0
        while len(results) < total and retries < 5:
            response = get_batch_of_tickets(start_at=len(results))
            total = response["total"]
            results += [f"{issue['key']} {issue['fields']['summary']}" for issue in response["issues"]]
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
            return None

        logger.debug(f"Posting work log to {issue_key[0]}")
        response = self.connector.add_worklog(
            issue_key=issue_key[0],
            detail=detail,
            at_datetime=at_datetime,
            interval=interval,
        )
        if response is None:
            logger.debug("Could not post work log, see above")
        elif response.status_code != 201:
            logger.debug(f"Response code: {response.status_code}")
            logger.debug(f"Could not post work log: {response.text}")


# Force into the Input/Output classes. This is naughty, but we'll fix it later
Jira(core.configuration.Configuration.from_default())
