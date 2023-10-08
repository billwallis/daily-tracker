"""
Post a message to a Slack channel.

The "Incoming Webhooks" option is easy to use (just post to the URL!),
but it's very limited and may be removed in a future version of Slack.

You can generate a webhook URL by navigating to the channel you want to
post to and configuring the "Incoming Webhooks" app.
"""
import json
import logging

import core
import requests


class SlackConnector:
    """
    Post a message to a Slack channel.
    """

    webhook_url: str

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def post_message(self, message: str) -> None:
        """
        Post a message to the configured channel using the Incoming Webhooks
        Slack app.

        The message can be formatted using Markdown.
        """
        payload = {
            "text": message,
            "username": "Daily Tracker",
            "icon_emoji": ":clock10:",
        }
        response = requests.post(url=self.webhook_url, data=json.dumps(payload))
        if response.status_code != 200:
            raise RuntimeError(
                f"{response.status_code}: Failed to post message to Slack\n\n{response.text}"
            )


class Slack(core.Output):
    """
    The Slack handler.

    This bridges the input and output objects with the REST API connector object
    to implement the output actions.
    """

    def __init__(self, url: str, configuration: core.Configuration = None):
        self.connector = SlackConnector(url)
        self.configuration = configuration

    def post_event(self, entry: core.Entry) -> None:
        """
        The actions to perform after the event.
        """
        logging.debug("Doing Slack actions...")
        if self.configuration.post_to_slack:
            self.post_to_channel(task=entry.task_name, detail=entry.detail)
            # Set status?

    def post_to_channel(self, task: str, detail: str) -> None:
        """
        Post the task details to a channel.

        The message accepts Markdown, so the task will be put in bold.
        """
        self.connector.post_message(f"*{task}*: {detail}")


if __name__ == "__main__":
    import os

    if slack_connector := SlackConnector(
        webhook_url=os.getenv("SLACK_WEBHOOK_URL")
    ):
        slack_connector.post_message(
            "This is a *test* success message with a link: <https://www.google.com|Google>"
        )
