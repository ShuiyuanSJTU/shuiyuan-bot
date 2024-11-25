from ..bot_account_manager import account_manager
from ..model import Post
from typing import Optional


def post_created_by_bot(post: Post):
    return post.username in account_manager.usernames


def post_mention_bot(post: Post, bot_username: Optional[str] = None):
    if bot_username is None:
        bot_username = account_manager.default_bot_client.username
    return f"@{bot_username}" in post.raw


def post_reply_to_bot(post: Post, bot_username: Optional[str] = None):
    if bot_username is None:
        bot_username = account_manager.default_bot_client.username
    return post.reply_to_user and post.reply_to_user.username == bot_username
