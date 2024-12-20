from .bot_config import config as Config
from .discourse_api import BotAPI
from .utils.singleton import Singleton
import logging

logger = logging.getLogger(__name__)

@Singleton
class BotAccountManager:
    def __init__(self):
        self.bot_clients: list[BotAPI] = []
        for bot_account in Config.bot_accounts:
            self.bot_clients.append(
                BotAPI(
                    base_url=Config.site_url,
                    username=bot_account.username,
                    api_key=bot_account.api_key,
                    raise_for_rate_limit=True
                )
            )
        if len(self.bot_clients) == 0:
            raise ValueError("No bot account is configured.")
        elif len(self.bot_clients) == 1:
            self._default_bot_client = self.bot_clients[0]
        else:
            default_bot_clients = list(
                filter(lambda x: x.default, Config.bot_accounts))
            if len(default_bot_clients) > 1:
                logger.warning(
                    "More than one bot account is marked as default, the first one will be used.")
                self._default_bot_client = self.bot_clients[Config.bot_accounts.index(default_bot_clients[0])]
            elif len(default_bot_clients) == 0:
                logger.warning(
                    "No bot account is marked as default, the first one will be used.")
                self._default_bot_client = self.bot_clients[0]
            else:
                self._default_bot_client = self.bot_clients[Config.bot_accounts.index(default_bot_clients[0])]

    @property
    def default_bot_client(self):
        return self._default_bot_client

    @property
    def usernames(self):
        return [bot_client.username for bot_client in self.bot_clients]

    def get_bot_client(self, username: str):
        for bot_client in self.bot_clients:
            if bot_client.username == username:
                return bot_client
        raise ValueError(f"Bot account with username {username} not found.")


account_manager = BotAccountManager()
