import json
import os
from unittest.mock import MagicMock, patch

import pytest

from backend.event_context import EventContext
from backend.model.post import Post


@pytest.fixture(scope="module")
def webhook_data():
    with open(os.path.join(os.path.dirname(__file__), "../data/test_model_post_data.json")) as f:
        return {"post": json.load(f)["webhook_with_reply_to"]}


@pytest.fixture
def mock_config(mock_config_base):
    mock_config_base.action_custom_config = {
        "BotPublicPostWebhookForward": {
            "enabled": True,
            "webhook_url": "https://example.com/webhook",
        }
    }
    return mock_config_base


@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config):
    yield


def create_action():
    from backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward import (
        BotPublicPostWebhookForward,
    )

    return BotPublicPostWebhookForward()


def create_event_context(webhook_data, raw_body=None, event_headers=None):
    return EventContext(
        event="post_created",
        raw_data=webhook_data,
        raw_body=raw_body if raw_body is not None else json.dumps(webhook_data).encode(),
        event_headers=event_headers or {"X-Discourse-Event": "post_created"},
    )


def test_forward_public_post_webhook(webhook_data):
    action = create_action()
    raw_body = json.dumps(webhook_data).encode()
    event_headers = {
        "X-Discourse-Event": "post_created",
        "X-Discourse-Event-Type": "post",
    }
    response = MagicMock(ok=True)

    with patch(
        "backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward.requests.post",
        return_value=response,
    ) as mock_post:
        action.on_post_created(
            Post(**webhook_data["post"]),
            event_context=create_event_context(webhook_data, raw_body, event_headers),
        )

    mock_post.assert_called_once_with(
        "https://example.com/webhook",
        data=raw_body,
        headers=event_headers,
        timeout=5,
    )


def test_skip_when_category_id_is_null(webhook_data):
    action = create_action()
    webhook_data = {"post": webhook_data["post"].copy()}
    webhook_data["post"]["category_id"] = None

    with patch(
        "backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward.requests.post",
    ) as mock_post:
        action.on_post_created(
            Post(**webhook_data["post"]),
            event_context=create_event_context(webhook_data),
        )

    mock_post.assert_not_called()


def test_skip_when_category_id_is_missing(webhook_data, caplog):
    action = create_action()
    webhook_data = {"post": webhook_data["post"].copy()}
    del webhook_data["post"]["category_id"]

    with patch(
        "backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward.requests.post",
    ) as mock_post:
        action.on_post_created(
            Post(**webhook_data["post"]),
            event_context=create_event_context(webhook_data),
        )

    mock_post.assert_not_called()
    assert "category_id is missing" in caplog.text


def test_forward_failure_does_not_raise(webhook_data, caplog):
    action = create_action()
    response = MagicMock(ok=False, status_code=500)

    with patch(
        "backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward.requests.post",
        return_value=response,
    ):
        action.on_post_created(
            Post(**webhook_data["post"]),
            event_context=create_event_context(webhook_data),
        )

    assert "status code 500" in caplog.text


def test_forward_exception_does_not_raise(webhook_data, caplog):
    action = create_action()

    with patch(
        "backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward.requests.post",
        side_effect=Exception("boom"),
    ):
        action.on_post_created(
            Post(**webhook_data["post"]),
            event_context=create_event_context(webhook_data),
        )

    assert "Forward public post webhook failed" in caplog.text


def test_missing_webhook_url_does_not_forward(patch_bot_config, webhook_data):
    patch_bot_config.action_custom_config["BotPublicPostWebhookForward"] = {
        "enabled": True,
    }
    action = create_action()

    with patch(
        "backend.plugins.bot_public_post_webhook_forward.bot_public_post_webhook_forward.requests.post",
    ) as mock_post:
        action.on_post_created(
            Post(**webhook_data["post"]),
            event_context=create_event_context(webhook_data),
        )

    mock_post.assert_not_called()
