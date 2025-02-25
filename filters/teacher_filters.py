import re
from datetime import timedelta, datetime, time

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete

from callback_factory.teacher_factories import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory
from database import Teacher, LessonWeek, LessonDay, Student, AccessTeacher
from database.models import Penalty
from database.teacher_requests import give_installed_lessons_week, give_penalty_by_teacher_id, \
    give_student_by_teacher_id
from services.services import give_list_with_days, give_date_format_callback, give_date_format_fsm, give_time_format_fsm


# Ученик - ничего не происходит
# Преподаватель - открываем
class TeacherStartFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery,
                       available_teachers):
        result = callback.from_user.id in available_teachers
        if not result:
            await callback.answer(text='Нет доступа!')
        return result


# Проверяем, находится учитель в базе данных или нет!
class IsTeacherInDatabase(BaseFilter):
    async def __call__(self, callback: Message, session: AsyncSession):
        stmt = select(Teacher).where(Teacher.teacher_id == callback.from_user.id)
        result = await session.execute(stmt)
        return result.scalar()


# Правильно ли введен номер телефона
class IsPhoneCorrectInput(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'\+7\d{10}', message.text)


# Правильно ли введен банк/банки
class IsBankCorrectInput(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'[A-zА-я]+/[A-zА-я]+', message.text) \
            or re.fullmatch(r'[A-zА-я]+', message.text)


# Правильно ли введено пенальти
class IsPenaltyCorrectInput(BaseFilter):
    async def __call__(self, message: Message):
        return message.text.isdigit() and int(message.text) >= 0


# Фильтр, который отлавливает апдейты, когда мы нажимаем на один из дней расписания
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


# Проверяем формат введенного времени ЧАСЫ:МИНУТЫ
class IsCorrectFormatTime(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'^0[0-9]:[0-5][0-9]|^1[0-9]:[0-5][0-9]|'
                            r'^2[0-3]:[0-5][0-9]', message.text)
        # re.fullmatch(r'\d\d:\d\d', message.text) and \


# Проверка, что время старта <23:30
class IsNewDayNotNear(BaseFilter):
    async def __call__(self, message: Message):
        give_time_format_fsm(message.text)
        return give_time_format_fsm(message.text) < time(hour=23, minute=30)


# Проверка, что время старта - время __пенальти__ > текущего времени
class IsCorrectTimeInputWithPenalty(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext,
                       session: AsyncSession):
        week_date_str = (await state.get_data())['week_date']
        week_date = give_date_format_fsm(week_date_str)
        time_put = give_time_format_fsm(message.text)
        penalty = await give_penalty_by_teacher_id(session,
                                                   message.from_user.id)
        dt_put = datetime(year=week_date.year,
                          month=week_date.month,
                          day=week_date.day,
                          hour=time_put.hour,
                          minute=time_put.minute)
        return datetime.now() + timedelta(hours=penalty) < dt_put


# Проверяем, что вводимое время больше текущего (по дню сравниванием также)
class IsInputTimeLongerThanNow(BaseFilter):
    async def __call__(self, message: Message, state):
        week_date_str = (await state.get_data())['week_date']
        week_date = give_date_format_fsm(week_date_str)
        time_add = give_time_format_fsm(message.text)
        return datetime.now() <= datetime(year=week_date.year,
                                          month=week_date.month,
                                          day=week_date.day,
                                          hour=time_add.hour,
                                          minute=time_add.minute)


# Фильтр проверяет, что время старта не конфликтует с уже добавленным
class IsNoConflictWithStart(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession, state: FSMContext):
        time_start = give_time_format_fsm(message.text)

        date_start_str = (await state.get_data())['week_date']
        date_start = give_date_format_fsm(date_start_str)

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


# Проверяем, что время_окончания - время_старта >= 30 минут
class IsDifferenceThirtyMinutes(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext):
        lesson_day_form = await state.get_data()

        work_start = give_time_format_fsm(lesson_day_form['work_start'])
        work_end = give_time_format_fsm(message.text)

        delta_start = timedelta(hours=work_start.hour, minutes=work_start.minute)
        delta_end = timedelta(hours=work_end.hour, minutes=work_end.minute)

        return delta_end - delta_start >= timedelta(minutes=30)


# Фильтр проверяет, что время старта < время_окончания
class IsNoEndBiggerStart(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext):
        lesson_day_form = await state.get_data()

        work_start = give_time_format_fsm(lesson_day_form['work_start'])
        work_end = give_time_format_fsm(message.text)

        return (timedelta(hours=work_end.hour, minutes=work_end.minute) >
                timedelta(hours=work_start.hour, minutes=work_start.minute))


# Проверка, что время окончания не лежит в уже существующем промежутке
class IsNoConflictWithEnd(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession, state: FSMContext):
        time_end = give_time_format_fsm(message.text)

        time_start_str = (await state.get_data())['work_start']
        time_start = give_time_format_fsm(time_start_str)

        date_end_str = (await state.get_data())['week_date']
        date_end = give_date_format_fsm(date_end_str)

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


class IsSomethingToShowSchedule(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession,
                       callback_data: ShowDaysOfPayCallbackFactory):
        week_date_str = callback_data.week_date
        week_date = give_date_format_fsm(week_date_str)

        result = await session.execute(
            select(LessonWeek.week_id)
            .where(LessonWeek.week_date == week_date)
        )

        return result.scalar()


class IsSomethingToPay(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession,
                       callback_data: ShowDaysOfPayCallbackFactory):
        week_date_str = callback_data.week_date
        week_date = give_date_format_fsm(week_date_str)

        result = await session.execute(
            select(LessonDay.lesson_id)
            .where(LessonDay.week_date == week_date)
        )

        return result.scalar()


class IsPenalty(BaseFilter):
    async def __call__(self, callback: CallbackQuery,
                       session: AsyncSession):
        is_penalty = await session.execute(
            select(Teacher.penalty)
            .where(Teacher.teacher_id == callback.from_user.id)
        )

        return is_penalty.scalar()
