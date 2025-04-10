import re
from datetime import timedelta, datetime, time

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from callback_factory.teacher_factories import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory
from database import Teacher, LessonWeek, LessonDay, Student, AccessTeacher, Debtor
from database.models import Penalty
from database.teacher_requests import give_installed_lessons_week, give_penalty_by_teacher_id, \
    give_student_by_teacher_id, give_all_lessons_day_by_week_day, give_list_debtors
from services.services import give_list_with_days, give_date_format_callback, give_date_format_fsm, give_time_format_fsm


# Ученик - ничего не происходит
# Преподаватель - открываем
class TeacherStartFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession):
        available_teachers = set(
            (await session.execute(select(AccessTeacher.teacher_id)
                                   .where(AccessTeacher.status == True))
             ).scalars().all()
        )
        result = callback.from_user.id in available_teachers
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
        return message.text.isdigit() and int(message.text) >= 0 \
    and int(message.text) == 0 #Отключаем систему пенальти

# Правильно ли введено время до уведомления о занятии
class IsUntilTimeNotification(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'[0-9][0-9]:[0-5][0-9]', message.text)

# Правильно ли введено время до уведомления о занятии
class IsDailyScheduleMailingTime(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'^0[0-9]:[0-5][0-9]|^1[0-9]:[0-5][0-9]|'
                            r'^2[0-3]:[0-5][0-9]', message.text)

class IsDailyReportMailingTime(BaseFilter):
    async def __call__(self, message: Message):
        return re.fullmatch(r'^0[0-9]:[0-5][0-9]|^1[0-9]:[0-5][0-9]|'
                            r'^2[0-3]:[0-5][0-9]', message.text)

class IsDaysCancellationNotification(BaseFilter):
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
# И если это не так, то отправляем время до пенальти, выбранное время
# НО МЫ ВСЕ ИНВЕРСИРУЕМ, ЧТОБЫ ПРИ НЕПРАВИЛЬНОМ ВРЕМЕНИ ПОЛУЧИТЬ ДАННЫЕ
class IsIncorrectTimeInputWithPenalty(BaseFilter):
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
        # if datetime.now() + timedelta(hours=penalty) < dt_put:
        if datetime.now() + timedelta(hours=penalty) >= dt_put:
            return {'dt_to_penalty': dt_put - timedelta(hours=penalty),
                    'dt_put': dt_put,
                    'time_penalty': penalty}
        return False


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


# Фильтр проверяет, что время старта конфликтует с уже добавленным
class IsConflictWithStart(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession, state: FSMContext):
        time_start = give_time_format_fsm(message.text)

        date_start_str = (await state.get_data())['week_date']
        date_start = give_date_format_fsm(date_start_str)

        res_time = (await give_installed_lessons_week(session,
                                                      message.from_user.id,
                                                      date_start)).all()

        if res_time:
            for one_date in res_time:
                delta_db = timedelta(hours=one_date.work_start.hour, minutes=one_date.work_start.minute)
                delta_cur = timedelta(hours=time_start.hour, minutes=time_start.minute)

                if one_date.work_start <= time_start < one_date.work_end or \
                        delta_db > delta_cur and delta_db - delta_cur < timedelta(minutes=30):
                    return {'res_time': res_time}
        # False - нет конфликта
        return False


# Проверяем, что время_окончания - время_старта < 30 минут
class IsDifferenceLessThirtyMinutes(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext):
        lesson_day_form = await state.get_data()

        work_start = give_time_format_fsm(lesson_day_form['work_start'])
        work_end = give_time_format_fsm(message.text)

        delta_start = timedelta(hours=work_start.hour, minutes=work_start.minute)
        delta_end = timedelta(hours=work_end.hour, minutes=work_end.minute)

        if delta_end - delta_start < timedelta(minutes=30):
            return {'work_start': work_start}
        return False


# Фильтр указывает выполняется ли время старта >= время_окончания
class IsEndBiggerStart(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext):
        lesson_day_form = await state.get_data()

        work_start = give_time_format_fsm(lesson_day_form['work_start'])
        work_end = give_time_format_fsm(message.text)

        # Время конца <= время старта
        if (timedelta(hours=work_end.hour, minutes=work_end.minute) <=
                timedelta(hours=work_start.hour, minutes=work_start.minute)):
            return {'work_start': work_start}
        else:
            return False


# Проверка, что время окончания лежит в уже существующем промежутке
class IsConflictWithEnd(BaseFilter):
    async def __call__(self, message: Message, session: AsyncSession, state: FSMContext):
        lesson_day_form = await state.get_data()

        time_start = give_time_format_fsm(lesson_day_form['work_start'])
        time_end = give_time_format_fsm(message.text)
        week_date = give_date_format_fsm(lesson_day_form['week_date'])

        res_time = (await give_installed_lessons_week(session,
                                                      message.from_user.id,
                                                      week_date)
                    ).all()

        if res_time:
            for one_date in res_time:
                if one_date.work_start < time_end <= one_date.work_end or \
                        time_start < one_date.work_start and time_end > one_date.work_end:
                    return {'work_start': time_start,
                            'work_end': time_end,
                            'res_time': res_time}
        return False


class IsRemoveNameRight(BaseFilter):
    async def __call__(self, callback: CallbackQuery):
        return callback.data[:-1] == 'del_record_teacher_' and callback.data[-1].isdigit()


class IsLessonWeekInDatabase(BaseFilter):
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

        result = (await session.execute(stmt)).scalar()

        if result:
            return {'week_date': week_date}
        return False


class IsSomethingToShowSchedule(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession,
                       callback_data: ShowDaysOfPayCallbackFactory):
        week_date_str = callback_data.week_date
        week_date = give_date_format_fsm(week_date_str)

        result = await give_all_lessons_day_by_week_day(session,
                                                        callback.from_user.id,
                                                        week_date)

        found_lessons_week = result.all()

        if found_lessons_week:
            return {'list_lessons_not_formatted': found_lessons_week,
                    'week_date_str': week_date_str}
        return False


class IsSomethingToPay(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession,
                       callback_data: ShowDaysOfPayCallbackFactory):
        week_date_str = callback_data.week_date
        week_date = give_date_format_fsm(week_date_str)

        result = await session.execute(
            select(LessonDay.lesson_id)
            .where(
                and_(
                    LessonDay.week_date == week_date,
                    LessonDay.teacher_id == callback.from_user.id
                )
            )
        )

        if result.scalar():
            return {'week_date_str': week_date_str,
                    'week_date': week_date}


class IsPenalty(BaseFilter):
    async def __call__(self, callback: CallbackQuery,
                       session: AsyncSession):
        is_penalty = await session.execute(
            select(Teacher.penalty)
            .where(Teacher.teacher_id == callback.from_user.id)
        )

        return is_penalty.scalar()


class IsNotTeacherAdd(BaseFilter):

    async def __call__(self, message: Message,
                       session: AsyncSession):
        teachers_access = await session.execute(
            select(AccessTeacher.teacher_id)
        )
        teachers_access_list = teachers_access.scalars().all()
        return int(message.text) not in teachers_access_list


class IsHasTeacherStudents(BaseFilter):

    async def __call__(self, callback: CallbackQuery, session: AsyncSession):
        has_students = (await session.execute(
            select(Student)
            .where(Student.teacher_id == callback.from_user.id)
            .options(selectinload(Student.access))
        )
                        ).scalars()

        if has_students:
            return {'list_students': has_students}
        return False

class IsDebtorsInDatabase(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession):
        list_debtors = await give_list_debtors(session, callback.from_user.id)
        if list_debtors:
            return {'list_debtors': list_debtors}
