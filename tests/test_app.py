import importlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock


def test_endpoint_passes_raw_body_and_discourse_headers(monkeypatch):
    mock_bot = MagicMock()
    mock_bot.BotManager.trigger_event.return_value = []
    mock_bot.Config.server = SimpleNamespace(
        discourse_instance_name="",
        whitelist_ips=[],
        reverse_proxy_ips=[],
        webhook_secret="",
    )

    mock_scheduler = MagicMock()
    mock_scheduler_module = MagicMock()
    mock_scheduler_module.BackgroundScheduler.return_value = mock_scheduler

    monkeypatch.setitem(sys.modules, "backend.bot", mock_bot)
    monkeypatch.setitem(
        sys.modules,
        "apscheduler.schedulers.background",
        mock_scheduler_module,
    )
    sys.modules.pop("app", None)
    app_module = importlib.import_module("app")

    client = app_module.app.test_client()
    raw_body = b'{"post":{"id":1,"category_id":2}}'
    response = client.post(
        "/",
        data=raw_body,
        content_type="application/json",
        headers={
            "X-Discourse-Event": "post_created",
            "X-Discourse-Event-Id": "event-id",
            "X-Other": "ignored",
        },
    )

    assert response.status_code == 200
    mock_bot.BotManager.trigger_event.assert_called_once()
    args, kwargs = mock_bot.BotManager.trigger_event.call_args
    assert args == ("post_created", {"post": {"id": 1, "category_id": 2}})
    assert kwargs["raw_body"] == raw_body
    assert kwargs["event_headers"] == {
        "X-Discourse-Event": "post_created",
        "X-Discourse-Event-Id": "event-id",
    }
    sys.modules.pop("app", None)
