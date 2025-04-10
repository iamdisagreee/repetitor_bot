import asyncio
import platform
from datetime import date, time

import taskiq
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from taskiq import TaskiqDepends, TaskiqState, TaskiqEvents, Context, ScheduledTask

from broker import worker, scheduler_storage
from config_data.config_data import load_config
from database import AccessStudent, Debtor

from aiogram.fsm.storage.redis import RedisStorage

from database.base import Base
from database.teacher_requests import delete_teacher_profile, remove_debtor_from_list_by_info
from handlers import teacher_handlers, everyone_handlers, student_handlers, other_handlers
from keyboards.everyone_kb import set_new_menu
from middlewares.outer import DbSessionMiddleware
from services.services import create_scheduled_task_handler
from services.services_taskiq import delete_all_schedules_teacher
from tasks import student_mailing_lessons, teacher_mailing_lessons

# from tasks import scheduled_payment_verification

config = load_config()

bot = Bot(token=config.tgbot.token,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


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
    # async with session_maker() as session:
    #     await remove_debtor_from_list_by_info(session,
    #                                           student_id=859717714,
    #                                           week_date=date.today(),
    #                                           lesson_on=time(0, 8),
    #                                           lesson_off=time(1, 8))
    #     debtor = Debtor(teacher_id=7880267101,
    #                     student_id=859717714,
    #                     week_date=date(2025, 4, 2),
    #                     lesson_on=time(11,30),
    #                     lesson_off=time(12, 30),
    #                     amount_money=1000)
    #     session.add(debtor)
    #     await session.commit()

    dp.include_router(everyone_handlers.router)
    dp.include_router(student_handlers.router)
    dp.include_router(teacher_handlers.router)
    dp.include_router(other_handlers.router)
    dp.update.outer_middleware(DbSessionMiddleware(session_maker))


    await worker.startup()
    await scheduler_storage.startup()
    # await delete_all_schedules_teacher(7880267101)
    # await create_scheduled_task_handler(task_name='student_mailing_lessons',
    #                                     schedule_id='student_mailing_lessons',
    #                                     cron='*/5 * * * *')
    # await create_scheduled_task_handler(task_name='teacher_mailing_lessons',
    #                                     schedule_id='teacher_mailing_status',
    #                                     cron='*/5 * * * *')

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
