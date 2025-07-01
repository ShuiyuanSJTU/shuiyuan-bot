import pytest
import json
import os.path

from backend.model.post import PostWebhook, PostAPI
from backend.model.user import BasicUser


@pytest.fixture(scope="module")
def test_data():
    with open(os.path.join(os.path.dirname(__file__), "data/test_model_post_data.json")) as f:
        return json.load(f)


def test_init_webhook_without_reply_to_user(test_data):
    post = PostWebhook(**test_data["webhook_without_reply_to"])
    assert post.id == 3512
    assert post.reply_to_user is None


def test_init_webhook_with_reply_to_user(test_data):
    post = PostWebhook(**test_data["webhook_with_reply_to"])
    assert post.id == 3859
    assert isinstance(post.reply_to_user, BasicUser)


def test_init_api(test_data):
    post = PostAPI(**test_data["api"])
    assert post.id == 994
    assert isinstance(post.reply_to_user, BasicUser)
