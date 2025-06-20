import taskiq_aiogram
from taskiq import TaskiqScheduler
from taskiq_nats import PullBasedJetStreamBroker, NATSObjectStoreResultBackend, NATSKeyValueScheduleSource

from bot.config_data.config_data import load_config

config_load = load_config()
worker = PullBasedJetStreamBroker(
    servers='localhost',
    queue='taskiq_queue').with_result_backend(
    result_backend=NATSObjectStoreResultBackend(servers=config_load.nats.token)
)

scheduler_storage = NATSKeyValueScheduleSource(servers=config_load.nats.token)
scheduler = TaskiqScheduler(worker, sources=[scheduler_storage])

taskiq_aiogram.init(
    worker,
    # This is path to the dispatcher.
    "bot.main:dp",
    # This is path to the bot instance.
    "bot.main:bot",
    # You can specify more bots here.
)