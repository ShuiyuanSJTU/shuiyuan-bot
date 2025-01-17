import os
import pkgutil
import importlib
import logging

from ..bot_action import BotAction
from ..db import db_manager as DBManager
from ..bot_manager import bot_manager as BotManager

def load_plugins():
    collected_actions = []
    package_path = os.path.dirname(__file__)

    for _, module_name, is_pkg in pkgutil.iter_modules([package_path]):
        if is_pkg and not module_name.startswith('_'):
            module = importlib.import_module(f"{__name__}.{module_name}")
            if hasattr(module, '__all__'):
                module_content = {name: getattr(
                    module, name) for name in module.__all__}
            else:
                module_content = {name: getattr(module, name) for name in dir(
                    module) if not name.startswith('_')}
            for obj in module_content.values():
                if isinstance(obj, type) and issubclass(obj, BotAction):
                    if obj.action_name != "BotActionBase":
                        collected_actions.append(obj)
                    elif not obj is BotAction:
                        logging.warning(
                            f"Class {obj} is a subclass of BotAction but does not have a valid action_name, so it is not registered.")
    for action_cls in collected_actions:
        BotManager.register_bot_action(action_cls)

