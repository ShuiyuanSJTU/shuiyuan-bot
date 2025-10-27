import pytest
from unittest.mock import MagicMock
from backend.model import Post
import os
import json
from copy import deepcopy


@pytest.fixture
def test_post():
    with open(os.path.join(os.path.dirname(__file__), "../data/test_model_post_data.json")) as f:
        return Post(**(json.load(f)['webhook_with_reply_to']))

@pytest.fixture(autouse=True)
def auto_patch(bypass_db_init):
    yield

@pytest.fixture
def mock_config(mock_config_base):
    mock_config_base.bot_accounts = [
        MagicMock(id=1, username="bot1", api_key="API_KEY_1",
                  writable=True, default=True),
    ]
    mock_config_base.action_custom_config = {
        "BotDice": {"enabled": True}
    }
    return mock_config_base


def test_bot_dice_init(patch_bot_config):
    from backend.plugins.bot_dice.bot_dice import BotDice
    bot_dice = BotDice()
    assert bot_dice.action_name == "BotDice"
    assert bot_dice.enabled is True


def test_bot_dice_should_reply(patch_bot_config, test_post):
    from backend.plugins.bot_dice.bot_dice import BotDice
    bot_dice = BotDice()
    post = deepcopy(test_post)
    assert bot_dice.should_response(post) is False
    post = deepcopy(test_post)
    post.raw = "@bot1 投掷\n1234"
    post.cooked = '<p><a class="mention" href="/u/bot1">@bot1</a> 投掷<br>1234</p>'
    assert bot_dice.should_response(post) is True


@pytest.mark.parametrize('input_str, expected_len', [
    ('5dGeom(0.5)', 5),
    ('3dN(0,1)', 3),
    ('4dU(0,10)', 4),
    ('6dB(10,0.5)', 6),
    ('2dPois(3)', 2),
    ('7dExp(1)', 7),
    ('5dGamma(2,2)', 5),
    ('8dBeta(2,5)', 8)
])
def test_parse_and_generate_advanced_random_numbers_geometric(patch_bot_config, input_str, expected_len):
    from backend.plugins.bot_dice.bot_dice import BotDice
    result = BotDice.parse_and_generate_advanced_random_numbers(
        "投掷 " + input_str)
    assert len(result) == expected_len


@pytest.mark.parametrize('input_str', [
    "5dX(0,1)",
    "5dN(0)",
    "5dU(0)",
    "21dN(0,1)",
    "5dN0,1)",
])
def test_parse_and_generate_advanced_random_numbers_invalid_input(patch_bot_config, input_str):
    from backend.plugins.bot_dice.bot_dice import BotDice
    with pytest.raises(ValueError):
        BotDice.parse_and_generate_advanced_random_numbers("投掷 " + input_str)
