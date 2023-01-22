"""
Connect to and read from a Jira project using its REST API:
    * https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/

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
import json
from typing import List

import requests


class JiraConnector:
    """
    Naive implementation of a connector to Jira via its REST API.

    This just exposes the Jira endpoints in a Pythonic way, but doesn't add any
    layers on top of this.
    """
    def __init__(self, url: str, key: str, secret: str):
        self._base_url = url
        self._api_key = key
        self._api_secret = secret

    @property
    def auth_basic(self) -> str:
        """
        Encode the key and secret using Basic Authentication.

        See more at the Atlassian documentation:
            https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/#supply-basic-auth-headers
        """
        return "Basic " + base64.b64encode(f"{self._api_key}:{self._api_secret}".encode("UTF-8")).decode()

    @property
    def auth_bearer(self) -> str:
        """
        Use bearer authentication (a personal access token).
        """
        return f"Bearer {self._api_secret}"

    @property
    def request_headers(self) -> dict:
        """
        Expose the default headers in a dictionary.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.auth_basic,
            # "Authorization": self.auth_bearer,
        }

    def get_projects_paginated(self, max_results: int = 50) -> requests.Response:
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
        fields: List[str],
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

    def add_worklog(self, issue_key: str, detail: str, at_datetime: str, interval: int) -> requests.Response:
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
        payload = json.dumps({
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
                        ]
                    }
                ]
            },
            "started": at_datetime
        })
        # payload = json.dumps({
        #     "comment": detail,
        #     "started": at_datetime,
        #     "timeSpentSeconds": interval * 60,
        # })
        return requests.request(
            method="POST",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            data=payload,
        )

    def create_issue(self, project_id: str, summary: str, description: str) -> requests.Response:
        """
        Call the "Create issue" endpoint of the API.

        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post
        """
        endpoint = "issue"
        payload = json.dumps({
            "update": {},
            "fields": {
                "summary": summary,
                "issuetype": {
                    "id": "10001"  # Task
                },
                "project": {
                    "id": project_id
                },
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
                            ]
                        }
                    ]
                },
                "labels": [],
                "duedate": None,
            }
        })
        return requests.request(
            method="POST",
            url=self._base_url + endpoint,
            headers=self.request_headers,
            data=payload,
        )
