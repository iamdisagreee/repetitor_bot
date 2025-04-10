import taskiq_aiogram
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from taskiq import TaskiqScheduler, TaskiqEvents, TaskiqState
from taskiq_nats import PullBasedJetStreamBroker, NATSObjectStoreResultBackend, NATSKeyValueScheduleSource

from config_data.config_data import load_config

worker = PullBasedJetStreamBroker(
    servers='localhost',
    queue='taskiq_queue').with_result_backend(
    result_backend=NATSObjectStoreResultBackend(servers='localhost')
)

scheduler_storage = NATSKeyValueScheduleSource(servers="localhost")
scheduler = TaskiqScheduler(worker, sources=[scheduler_storage])

taskiq_aiogram.init(
    worker,
    # This is path to the dispatcher.
    "main:dp",
    # This is path to the bot instance.
    "main:bot",
    # You can specify more bots here.
)

@worker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    config = load_config()
    engine = create_async_engine(url=config.tgbot.postgresql,
                                 echo=False)
    state.session_pool = async_sessionmaker(engine)