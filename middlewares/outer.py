from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from database import AccessTeacher, AccessStudent
from database.base import Base
from database.models.penalties import Penalty


# Открываем сессию для SQLAlchemy
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]):

        async with self.session_pool() as session:
            available_teachers = await session.execute(select(AccessTeacher.teacher_id)
                                                       .where(AccessTeacher.status == True))
            available_students = await session.execute(select(AccessStudent.student_id)
                                                       .where(AccessStudent.status == True))
            data["available_teachers"] = [teacher for teacher
                                          in available_teachers.scalars()]
            data["available_students"] = [student for student in
                                          available_students.scalars()]
            data["session"] = session
            return await handler(event, data)

