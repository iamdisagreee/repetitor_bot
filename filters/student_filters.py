import re
from datetime import timedelta, datetime
from pprint import pprint
from typing import Dict, Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from pydantic import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database import Student, LessonWeek, LessonDay
from database.student_requirements import give_lessons_week_for_day, give_all_busy_time_intervals, \
    give_teacher_id_by_student_id
from services.services import give_list_with_days, give_date_format_fsm, create_choose_time_student


class IsStudentInDatabase(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession):
        stmt = select(Student).where(Student.student_id == message.from_user.id)
        result = await session.execute(stmt)
        return result.scalar()


class IsInputFieldAlpha(BaseFilter):
    async def __call__(self, message: Message):
        return message.text.isalpha()


class IsInputFieldDigit(BaseFilter):
    async def __call__(self, message: Message):
        return message.text.isdigit()


class FindNextSevenDaysFromKeyboard(BaseFilter):
    async def __call__(self, callback: CallbackQuery):
        my_days = [
            cur_date.strftime('%Y-%m-%d') for cur_date in give_list_with_days(datetime.now())
        ]
        return callback.data in my_days


class IsMoveRightAddMenu(BaseFilter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext, session: AsyncSession):
        state_dict = await state.get_data()
        week_date_str = state_dict['week_date']
        week_date = give_date_format_fsm(week_date_str)
        lessons_week = await give_lessons_week_for_day(session, week_date)

        teacher_id = await give_teacher_id_by_student_id(session,
                                                         callback.from_user.id)
        lessons_busy = await give_all_busy_time_intervals(session,
                                                          teacher_id,
                                                          week_date)

        dict_lessons = create_choose_time_student(lessons_week, lessons_busy)

        page = 0
        for day, times in dict_lessons.items():
            if not times:
                page = day
                break

        return (await state.get_data())['page'] + 1 < page


class IsMoveLeftAddMenu(BaseFilter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext, session: AsyncSession):
        return (await state.get_data())['page'] - 1 >= 1


class IsTeacherDidSlots(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        state_dict = await state.get_data()
        week_date = give_date_format_fsm(state_dict['week_date'])
        teacher_id = await give_teacher_id_by_student_id(session,
                                                         callback.from_user.id)

        result = await session.execute(
            select(LessonWeek)
            .where(
                and_(LessonWeek.week_date == week_date,
                     LessonWeek.teacher_id == teacher_id)
            )
        )
        # print(week_date, teacher_id)
        return result.scalar()


class IsStudentChooseSlots(BaseFilter):

    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        state_dict = await state.get_data()
        week_date = give_date_format_fsm(state_dict['week_date'])
        result = await session.execute(
            select(LessonDay)
            .where(
                and_(
                    LessonDay.student_id == callback.from_user.id,
                    LessonDay.week_date == week_date
                )
            )
        )
        return result.scalar()
