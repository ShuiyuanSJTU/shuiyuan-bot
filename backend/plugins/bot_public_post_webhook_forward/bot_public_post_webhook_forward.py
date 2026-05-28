import logging
from typing import Any, Optional

import requests

from ...bot_action import BotAction, on
from ...model.post import Post

logger = logging.getLogger(__name__)


class BotPublicPostWebhookForward(BotAction):
    action_name = "BotPublicPostWebhookForward"
    default_timeout_seconds = 5

    def __init__(self):
        self.webhook_url: Optional[str] = None
        self.timeout_seconds: int = self.default_timeout_seconds
        super().__init__()
        if self.enabled:
            self.webhook_url = self.config.get("webhook_url")
            self.timeout_seconds = self.config.get(
                "timeout_seconds",
                self.default_timeout_seconds,
            )
            if not self.webhook_url:
                logger.warning("BotPublicPostWebhookForward is enabled but webhook_url is not configured.")

    @on("post_created")
    def on_post_created(
        self,
        post: Post,
        raw_data: Optional[dict[str, Any]] = None,
        raw_body: Optional[bytes] = None,
        event_headers: Optional[dict[str, str]] = None,
    ):
        if not self.webhook_url:
            return

        raw_post = (raw_data or {}).get("post", {})
        if "category_id" not in raw_post:
            logger.warning("Skip forwarding post_created webhook because category_id is missing.")
            return

        if raw_post["category_id"] is None:
            return

        if raw_body is None:
            logger.warning("Skip forwarding post_created webhook because raw_body is missing.")
            return

        self.forward_webhook(raw_body, event_headers or {})

    def forward_webhook(self, raw_body: bytes, event_headers: dict[str, str]):
        headers = dict(event_headers)
        try:
            response = requests.post(
                self.webhook_url,
                data=raw_body,
                headers=headers,
                timeout=self.timeout_seconds,
            )
            if not response.ok:
                logger.warning(
                    "Forward public post webhook failed with status code %s.",
                    response.status_code,
                )
        except Exception:
            logger.exception("Forward public post webhook failed.")
