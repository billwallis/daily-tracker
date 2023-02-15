"""
Connect to a Slack workspace using its SDK:
    * https://slack.dev/python-slack-sdk/

Note that:
    * The KEY should be your email address for your Atlassian account
    * The SECRET should be a token that you generate for your Atlassian account
See more at:
    * https://id.atlassian.com/manage-profile/security/api-tokens
"""
import slack_sdk


class SlackConnector:
    """
    Naive implementation of a connector to Slack via its SDK.
    """
    def __init__(
        self,
        url: str,
        # token: str,
    ):
        self._base_url = url
        # self._api_token = token
        self.client = slack_sdk.WebhookClient(url=self._base_url)

    def post_to_channel(self, message: str) -> None:
        """
        Post to the linked channel.
        """
        self.client.send(text=message)

    def _post_to_channel(self, message: str) -> None:
        """
        Post to the linked channel.

        Check out:
        * https://api.slack.com/messaging/webhooks#advanced_message_formatting
        * https://api.slack.com/block-kit
        """
        self.client.send(
            text=message,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Danny Torrence left the following review for your property:",
                    }
                },
                {
                    "type": "section",
                    "block_id": "section567",
                    "text": {
                        "type": "mrkdwn",
                        "text": "<https://example.com|Overlook Hotel> \n :star: \n Doors had too many axe holes, guest in room 237 was far too rowdy, whole place felt stuck in the 1920s.",
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": "https://is5-ssl.mzstatic.com/image/thumb/Purple3/v4/d3/72/5c/d3725c8f-c642-5d69-1904-aa36e4297885/source/256x256bb.jpg",
                        "alt_text": "Haunted hotel image",
                    }
                },
                {
                    "type": "section",
                    "block_id": "section789",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Average Rating*\n1.0",
                        }
                    ]
                }
            ],
        )
