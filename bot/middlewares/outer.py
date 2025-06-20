from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.database import AccessTeacher, AccessStudent


# Открываем сессию для SQLAlchemy
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]):
        async with self.session_pool() as session:
            available_teachers = set(
                (await session.execute(select(AccessTeacher.teacher_id)
                                       .where(AccessTeacher.status == True))
                 ).scalars().all()
            )
            available_students = set(
                (await session.execute(select(AccessStudent.student_id)
                                       .where(AccessStudent.status == True)
                                       )
                 ).scalars().all()
            )
            data["available_teachers"] = available_teachers
            data["available_students"] = available_students
            data["session"] = session
            return await handler(event, data)
