import re
from datetime import timedelta, datetime
from pprint import pprint
from typing import Dict, Any

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from callback_factory.teacher import ShowDaysOfPayCallbackFactory
from database import Teacher, LessonWeek, LessonDay
from database.teacher_requirements import give_installed_lessons_week
from services.services import give_list_with_days, give_date_format_callback, give_date_format_fsm, give_time_format_fsm


class IsTeacherInDatabase(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession):
        stmt = select(Teacher).where(Teacher.teacher_id == message.from_user.id)
        result = await session.execute(stmt)
        # print(result.scalar() is None)
        return result.scalar()


class FindNextSevenDaysFromKeyboard(BaseFilter):
    async def __call__(self, callback: CallbackQuery):
        my_days = [
            cur_date.strftime('%Y-%m-%d') for cur_date in give_list_with_days(datetime.now())
        ]
        return callback.data in my_days


class IsLessonWeekInDatabaseCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession):
        format_date = give_date_format_callback(callback.data)
        stmt = (
            select(LessonWeek)
            .where(
                and_(
                    LessonWeek.week_date == format_date,
                    LessonWeek.teacher_id == callback.from_user.id
                )
            )
        )
        result = await session.execute(stmt)
        return result.scalar()


class IsCorrectFormatInput(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'\d\d:\d\d', message.text)


class IsDifferenceThirtyMinutes(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext):
        lesson_day_form = await state.get_data()

        work_start = give_time_format_fsm(lesson_day_form['work_start'])
        work_end = give_time_format_fsm(message.text)

        delta_start = timedelta(hours=work_start.hour, minutes=work_start.minute)
        delta_end = timedelta(hours=work_end.hour, minutes=work_end.minute)

        return delta_end - delta_start >= timedelta(minutes=30)


class IsNoEndBiggerStart(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext):
        lesson_day_form = await state.get_data()

        work_start = give_time_format_fsm(lesson_day_form['work_start'])
        work_end = give_time_format_fsm(message.text)

        return (timedelta(hours=work_end.hour, minutes=work_end.minute) >
                timedelta(hours=work_start.hour, minutes=work_start.minute))


class IsNoConflictWithStart(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession, state: FSMContext):
        time_start = give_time_format_fsm(message.text)

        date_start_str = (await state.get_data())['week_date']
        date_start = give_date_format_fsm(date_start_str)

        # res_time = await session.execute(
        #     select(LessonWeek)
        #     .where(
        #         and_(
        #             LessonWeek.teacher_id == message.from_user.id,
        #             LessonWeek.week_date == date_start
        #         )
        #     )
        # )
        res_time = await give_installed_lessons_week(session,
                                                     message.from_user.id,
                                                     date_start)

        if res_time:
            for one_date in res_time:
                delta_db = timedelta(hours=one_date.work_start.hour, minutes=one_date.work_start.minute)
                delta_cur = timedelta(hours=time_start.hour, minutes=time_start.minute)

                if one_date.work_start <= time_start < one_date.work_end or \
                        delta_db > delta_cur and delta_db - delta_cur < timedelta(minutes=30):
                    return False
        return True


class IsNoConflictWithEnd(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession, state: FSMContext):
        time_end = give_time_format_fsm(message.text)

        time_start_str = (await state.get_data())['work_start']
        time_start = give_time_format_fsm(time_start_str)

        date_end_str = (await state.get_data())['week_date']
        date_end = give_date_format_fsm(date_end_str)

        # res_time = await session.execute(
        #     select(LessonWeek)
        #     .where(
        #         and_(
        #             LessonWeek.teacher_id == message.from_user.id,
        #             LessonWeek.week_date == date_end
        #         )
        #     )
        # )

        res_time = await give_installed_lessons_week(session,
                                                     message.from_user.id,
                                                     date_end)

        if res_time:
            for one_date in res_time:
                if one_date.work_start < time_end <= one_date.work_end or \
                        time_start < one_date.work_start and time_end > one_date.work_end:
                    return False
        return True


class IsRemoveNameRight(BaseFilter):
    async def __call__(self, callback: CallbackQuery):
        return callback.data[:-1] == 'del_record_teacher_' and callback.data[-1].isdigit()


class IsLessonWeekInDatabaseState(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        week_date_str = (await state.get_data())['week_date']
        week_date = give_date_format_fsm(week_date_str)

        stmt = (
            select(LessonWeek)
            .where(
                and_(
                    LessonWeek.week_date == week_date,
                    LessonWeek.teacher_id == callback.from_user.id
                )
            )
        )

        result = await session.execute(stmt)

        return result.scalar()


class IsSomethingToConfirm(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession,
                       callback_data: ShowDaysOfPayCallbackFactory):

        week_date_str = callback_data.week_date
        week_date = give_date_format_fsm(week_date_str)

        result = await session.execute(
            select(LessonDay.lesson_id)
            .where(LessonDay.week_date == week_date)
        )

        return result.scalar()
