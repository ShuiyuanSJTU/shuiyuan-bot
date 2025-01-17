from . import plugins
plugins.load_plugins()

from .bot_manager import bot_manager as BotManager
from .bot_config import config as Config