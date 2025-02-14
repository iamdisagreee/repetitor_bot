import asyncio
import platform

from aiogram import Bot, Dispatcher
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from config_data.config import load_config
from database.base import Base

from datetime import datetime

from sqlalchemy import BigInteger, func, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase
from aiogram.fsm.storage.redis import RedisStorage
from handlers import teacher_handlers, everyone_handlers, student_handlers
from middlewares.outer import DbSessionMiddleware


async def main():
    config = load_config()

    engine = create_async_engine(url=config.tgbot.postgresql,
                                 echo=False)

    storage = RedisStorage.from_url('redis://default:amazingroom123@176.109.110.166:6379/1')

    async with engine.begin() as session:
        await session.execute(text('SELECT 1'))

    # print("МОИ МОДЕЛИ")
    # for table_name in Base.metadata.tables.keys():
    #     print(table_name)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    bot = Bot(token=config.tgbot.token)
    dp = Dispatcher(storage=storage)

    session_maker = async_sessionmaker(engine)

    dp.include_router(teacher_handlers.router)
    dp.include_router(everyone_handlers.router)
    dp.include_router(student_handlers.router)

    dp.update.outer_middleware(DbSessionMiddleware(session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
