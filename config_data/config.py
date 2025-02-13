from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    postgresql: str
    redis: str


@dataclass
class Config:
    tgbot: TgBot


def load_config():
    env = Env()
    env.read_env()
    return Config(tgbot=TgBot(token=env('BOT_TOKEN'),
                              postgresql=env('DSN_POSTGRESQL'), #DATA SOURCE NAME
                              redis=env('DSN_REDIS')))
