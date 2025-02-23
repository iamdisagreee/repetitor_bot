from pprint import pprint
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from database import AccessTeacher, AccessStudent


# Открываем сессию
# Кеширование?????
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]):
        # print(event.model_dump_json(indent=4))
        # user_id = event.callback_query.from_user.id
        # if isinstance(event, CallbackQuery):
        #     pass
        # print(event.from_user.id)
        # print('123123123123123123132')

        async with self.session_pool() as session:
            available_teachers = await session.execute(select(AccessTeacher.teacher_id)
                                                       .where(AccessTeacher.status == True))
            available_students = await session.execute(select(AccessStudent.student_id)
                                                       .where(AccessStudent.status == True))
            data["available_teachers"] = [teacher for teacher
                                          in available_teachers.scalars()]
            data["available_students"] = [student for student in
                                          available_students.scalars()]
           # print('Учителя:',data["available_teachers"])
           # print('Студенты:', data['available_students'])
            # print([x for x in available_students.scalars()])
            # print(859717714 in data["available_students"],
            #       859717714 in data["available_teachers"])

            # print(data["available_students"])
            data["session"] = session
            return await handler(event, data)


# class IsAccessTeacherMiddleware(BaseMiddleware):
#     async def __call__(self,
#                        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
#                        event: TelegramObject,
#                        data: Dict[str, Any]):
#         print('t ',event.from_user.id in data['available_teachers'])
#         if event.from_user.id in data['available_teachers']:
#             return await handler(event, data)
#         else:
#             await event.answer("Нет доступа!")


# class IsAccessUserMiddleware(BaseMiddleware):
#     async def __call__(self,
#                        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
#                        event: TelegramObject,
#                        data: Dict[str, Any]):
#         #print('s ', event.from_user.id, data['available_students'])
#         if event.from_user.id in data['available_students']:
#             return await handler(event, data)
#         elif event.from_user.id in data['available_teachers']:
#             return await handler(event, data)
#         await event.answer("Нет доступа!")
