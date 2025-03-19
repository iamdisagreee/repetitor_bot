import asyncio
import platform

import taskiq
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from taskiq import TaskiqDepends, TaskiqState, TaskiqEvents, Context, ScheduledTask

from broker import worker, scheduler_storage
from config_data.config_data import load_config
from database import AccessStudent

from aiogram.fsm.storage.redis import RedisStorage

from database.base import Base
from handlers import teacher_handlers, everyone_handlers, student_handlers, other_handlers
from keyboards.everyone_kb import set_new_menu
from middlewares.outer import DbSessionMiddleware
# from tasks import scheduled_payment_verification

config = load_config()

bot = Bot(token=config.tgbot.token,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@worker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(state: TaskiqState) -> None:
    config = load_config()
    engine = create_async_engine(url=config.tgbot.postgresql,
                                 echo=False)
    state.session_pool = async_sessionmaker(engine)


@worker.task
async def daily_payment_check(context: Context = TaskiqDepends(),
                              bot: Bot = TaskiqDepends(),
                              ):
    async with context.state.session_pool() as session:
        res = await session.execute(select(AccessStudent.student_id))
    await bot.send_message(859717714, str(res.scalar()))


async def main():
    config = load_config()

    # Создаем асинхронный движок sqlalchemy
    engine = create_async_engine(url=config.tgbot.postgresql,
                                 echo=False)

    # async with engine.begin() as connection:
    #      await connection.run_sync(Base.metadata.drop_all)
    #      print("Удалил")
    #      await connection.run_sync(Base.metadata.create_all)
    #      print("Создал")

    # Создаем хранилище redis для FSM
    storage = RedisStorage.from_url(config.tgbot.redis)
    # Устанавливаем вываливающуюся клавиатуру
    await set_new_menu(bot)

    session_maker = async_sessionmaker(engine)

    dp.include_router(everyone_handlers.router)
    dp.include_router(student_handlers.router)
    dp.include_router(teacher_handlers.router)
    dp.include_router(other_handlers.router)
    dp.update.outer_middleware(DbSessionMiddleware(session_maker))

    # worker.add_dependency_context({
    #     "session_pool": session_maker,
    # })

    await worker.startup()

    await scheduler_storage.startup()
    # await scheduled_payment_verification.kiq()
    # Логика настройки проверки оплаты в 23:50 по мск
    # await scheduler_storage.add_schedule(
    #     ScheduledTask(
    #         task_name='scheduled_payment_verification',
    #         labels={},
    #         args=[],
    #         kwargs={},
    #         cron='*/1 * * * *',
    #         cron_offset='Europe/Moscow',
    #         # time=datetime(2025, 3, 10, 18, 10),
    #         # time=datetime.now(timezone.utc) + timedelta(seconds=10),
    #         schedule_id=f'scheduled_payment_verification',
    #     )
    # )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(
        bot,
        storage=storage,
        scheduler_storage=scheduler_storage
    )
    await worker.shutdown()
    await scheduler_storage.shutdown()


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
