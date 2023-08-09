"""
Post a message to a Slack channel.

The "Incoming Webhooks" option is easy to use (just post to the URL!),
but it's very limited and may be removed in a future version of Slack.

You can generate a webhook URL by navigating to the channel you want to
post to and configuring the "Incoming Webhooks" app.
"""
import json

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


if __name__ == "__main__":
    import os

    if slack_connector := SlackConnector(
        webhook_url=os.getenv("SLACK_WEBHOOK_URL")
    ):
        slack_connector.post_message(
            "This is a *test* success message with a link: <https://www.google.com|Google>"
        )
