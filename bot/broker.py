import taskiq_aiogram
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from taskiq import TaskiqScheduler, TaskiqEvents, TaskiqState
from taskiq_nats import PullBasedJetStreamBroker, NATSObjectStoreResultBackend, NATSKeyValueScheduleSource

from bot.config_data.config_data import load_config

config_load = load_config()
worker = PullBasedJetStreamBroker(
    servers=config_load.nats.token,
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


@worker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    # await worker.startup()
    await scheduler_storage.startup()
    config = load_config()
    engine = create_async_engine(url=config.postgres.token,
                                 echo=False)
    state.session_pool = async_sessionmaker(engine)

@worker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(state: TaskiqState) -> None:
    await scheduler_storage.shutdown()
    # await worker.shutdown()
