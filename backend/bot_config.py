from pydantic import BaseModel
from typing import Any
import os
import yaml
import logging

config = None


class ServerConfig(BaseModel):
    enabled: bool = True
    bind_address: str = "0.0.0.0"
    bind_port: int = 80
    webhook_secret: str = ""
    discourse_instance_name: str = ""
    whitelist_ips: list[str] = []
    reverse_proxy_ips: list[str] = []


class BotAccount(BaseModel):
    id: int
    username: str
    api_key: str
    writable: bool
    default: bool = False


class BotConfig(BaseModel):
    site_url: str
    limited_mode: bool = False
    limited_usernames: list[str] = []
    redis_host: str = ""
    redis_port: int = 6379
    server: ServerConfig = ServerConfig()
    bot_accounts: list[BotAccount]
    action_custom_config: dict[str, dict[str, Any]]


def load_config(file_path: str) -> BotConfig:
    with open(file_path, 'r') as file:
        config_dict = yaml.safe_load(file)
    return BotConfig(**config_dict)


def init_config_file(file_path: str):
    config = BotConfig(
        site_url="https://example.com",
        bind_address="0.0.0.0",
        bind_port=80,
        bot_accounts=[
            BotAccount(
                id=0,
                username="bot",
                api_key="API_KEY",
                writable=True,
                default=True
            )
        ],
        action_custom_config={
            "action_name": {
                "enabled": True,
                "key": "value"
            }
        }
    )
    with open(file_path, 'w') as file:
        yaml.dump(config.model_dump(), file, sort_keys=False)


def init(config_file: str = "config.yaml"):
    global config
    if config is not None:
        logging.warning("Config already initialized")
        return
    if not os.path.exists(config_file):
        init_config_file(config_file)
        logging.warning(
            f"Config file not found, created a new one at {config_file}")
        exit(0)
    else:
        config = load_config(config_file)


if __name__ == "__main__":
    init("config.yaml")
    print(config)
else:
    init("config.yaml")
    logging.info("Config initialized")
