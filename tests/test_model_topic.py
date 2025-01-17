import pytest
import json
import os.path

from backend.model.topic import Topic
from backend.model.user import BasicUser


@pytest.fixture(scope="module")
def test_data():
    with open(os.path.join(os.path.dirname(__file__), "data/test_model_topic_data.json")) as f:
        return json.load(f)


def test_init_topic(test_data):
    topic = Topic(**test_data["topic"])
    assert topic.id == 25
    assert isinstance(topic.created_by, BasicUser)
