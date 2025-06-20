import asyncio
import platform

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from bot.broker import worker, scheduler_storage
from bot.config_data.config_data import load_config

from aiogram.fsm.storage.redis import RedisStorage

from bot.handlers import other_handlers, teacher_handlers, everyone_handlers, student_handlers
from bot.keyboards.everyone_kb import set_new_menu
from bot.middlewares.outer import DbSessionMiddleware
from bot.services.services import create_scheduled_task_handler

config = load_config()

bot = Bot(token=config.tgbot.token,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def main():

    # Создаем асинхронный движок sqlalchemy
    engine = create_async_engine(url=config.postgres.token,
                                 echo=False)

    # async with engine.begin() as connection:
    #      await connection.run_sync(Base.metadata.drop_all)
    #      print("Удалил")
    #      await connection.run_sync(Base.metadata.create_all)
    #      print("Создал")

    # Создаем хранилище redis для FSM
    storage = RedisStorage.from_url(config.redis.token)
    # Устанавливаем вываливающуюся клавиатуру
    await set_new_menu(bot)

    session_maker = async_sessionmaker(engine)

    dp.include_router(everyone_handlers.router)
    dp.include_router(student_handlers.router)
    dp.include_router(teacher_handlers.router)
    dp.include_router(other_handlers.router)
    dp.update.outer_middleware(DbSessionMiddleware(session_maker))


    await worker.startup()
    await scheduler_storage.startup()
    await create_scheduled_task_handler(task_name='student_mailing_lessons',
                                        schedule_id='student_mailing_lessons',
                                        cron='*/2 * * * *')
    await create_scheduled_task_handler(task_name='teacher_mailing_lessons',
                                        schedule_id='teacher_mailing_status',
                                        cron='*/2 * * * *')

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
