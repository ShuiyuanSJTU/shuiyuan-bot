from . import plugins
plugins.load_plugins()

from .db import db_manager as DBManager
DBManager.init_tables()

from .bot_manager import bot_manager as BotManager
from .bot_config import config as Config