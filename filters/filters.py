import re
from datetime import timedelta, datetime
from pprint import pprint
from typing import Dict, Any
from aiogram.types import Message
from aiogram.filters import BaseFilter
from pydantic import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database import Teacher, LessonWeek
from services.services import give_dict_with_days, create_date_record


class IsTeacherInDatabase(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession):
        # pprint(data, compact=True)
        # print(data)
        # data_json = data.model_dump_json(indent=4)
        # print(data_json)
        # session = data_json['session']
        stmt = select(Teacher).where(Teacher.teacher_id == message.from_user.id)
        result = await session.execute(stmt)
        # print(result.scalar() is None)
        return result.scalar()


class FindNextSevenDaysFromKeyboard(BaseFilter):
    async def __call__(self, message: Message):
        my_days = [f'{date} - {name}' for date, name
                   in give_dict_with_days(datetime.now() + timedelta(days=1)).items()]
        return message.text in my_days


class IsLessonWeekInDatabase(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession):
        format_date = create_date_record(message.text)
        print(format_date)
        stmt = (
            select(LessonWeek)
            .where(
                and_(
                    LessonWeek.week_date == format_date,
                    LessonWeek.teacher_id == message.from_user.id
                )
            )
        )
        result = await session.execute(stmt)
        return result.scalar()


class IsCorrectTimeInput(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'\d\d:\d\d', message.text)
