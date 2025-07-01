# ruff: noqa

from . import plugins
plugins.load_plugins()

# initialize bot manager and config
from .bot_manager import bot_manager as BotManager
from .bot_config import config as Config

__all__ = [
    "BotManager",
    "Config",
]