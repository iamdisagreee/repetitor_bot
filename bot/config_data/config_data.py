from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class NatsConf:
    token: str


@dataclass
class PostgresConf:
    token: str


@dataclass
class RedisConf:
    token: str


@dataclass
class Config:
    tgbot: TgBot
    nats: NatsConf
    postgres: PostgresConf
    redis: RedisConf


def load_config():
    env = Env()
    env.read_env()
    return Config(tgbot=TgBot(token=env('BOT_TOKEN')),
                  nats=NatsConf(token=env('NATS_SERVER')),
                  postgres=PostgresConf(token=env('DSN_POSTGRESQL')),
                  redis=RedisConf(token=env('DSN_REDIS'))
                  )
