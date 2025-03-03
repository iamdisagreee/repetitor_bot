import asyncio
import platform

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, select, inspect
from config_data.config import load_config
from database import LessonWeek
from database.base import Base

from datetime import datetime, timedelta, date

from sqlalchemy import BigInteger, func, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
from aiogram.fsm.storage.redis import RedisStorage
from handlers import teacher_handlers, everyone_handlers, student_handlers
from keyboards.everyone_kb import set_new_menu
from lexicon import other_handlers
from middlewares.outer import DbSessionMiddleware
from apscheduler.schedulers.background import BackgroundScheduler


async def delete_old_records(session_maker: async_sessionmaker):
    dt = datetime.now()
    one_day_ago_date = date(year=dt.year, month=dt.month, day=dt.day)
    async with session_maker() as session:
        result = await session.execute(select(LessonWeek)
                                       .where(LessonWeek.week_date < one_day_ago_date))
        for day in result.scalars():
            await session.delete(day)
        await session.commit()


async def main():
    config = load_config()

    engine = create_async_engine(url=config.tgbot.postgresql,
                                 echo=False)

    storage = RedisStorage.from_url(config.tgbot.redis)

    # print("МОИ МОДЕЛИ")
    # for table_name in Base.metadata.tables.keys():
    #     print(table_name)
    # async with engine.begin() as session:
    #     await session.execute(text('SELECT 1'))

    # async with engine.begin() as connection:
    #      await connection.run_sync(Base.metadata.drop_all)
    #      print("Удалил")
    #      await connection.run_sync(Base.metadata.create_all)
    #      print("Создал")

    bot = Bot(token=config.tgbot.token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Устанавливаем вываливающуюся клавиатуру
    await set_new_menu(bot)

    dp = Dispatcher(storage=storage)

    session_maker = async_sessionmaker(engine)

    dp.include_router(everyone_handlers.router)
    dp.include_router(student_handlers.router)
    dp.include_router(teacher_handlers.router)
    dp.include_router(other_handlers.router)
    dp.update.outer_middleware(DbSessionMiddleware(session_maker))

    # Удаление по расписанию (раз в 3 дня)!
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(delete_old_records, 'interval', days=3, args=(session_maker,))  # Runs daily
    # scheduler.start()
    # await bot.send_message(chat_id=822208465,text='Бу! Испугался?\n'
    #                                               'Не бойся! Это я - твой друг!\n'
    #                                               'Щавель или персик?')

    await bot.delete_webhook(drop_pending_updates=True)
    print("START POLLING...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
