import time
from datetime import timedelta, datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from callback_factory.student_factories import ShowDaysOfScheduleCallbackFactory, DeleteFieldCallbackFactory
from database import Student, LessonWeek, LessonDay
from database.models import Penalty
from database.student_requests import give_lessons_week_for_day, give_all_busy_time_intervals, \
    give_teacher_by_student_id, give_all_lessons_for_day
from services.services import give_list_with_days, give_date_format_fsm, create_choose_time_student, \
    create_delete_time_student, give_time_format_fsm


# Преподаватель - нет доступа
# Ученик - открываем
class StudentStartFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery,
                       available_students):
        result = callback.from_user.id in available_students
        # if not result:
        #     await callback.answer()
        return result


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


class IsRightClassCourse(BaseFilter):
    async def __call__(self, message: Message):
        return message.text.isdigit() and 1 <= int(message.text) <= 11


class IsRightPrice(BaseFilter):
    async def __call__(self, message):
        return message.text.isdigit() and int(message.text) >= 0


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

        student = await give_teacher_by_student_id(session,
                                                   callback.from_user.id)
        lessons_week = await give_lessons_week_for_day(session, week_date,
                                                       student.teacher_id)

        lessons_busy = await give_all_busy_time_intervals(session,
                                                          student.teacher_id,
                                                          week_date)

        dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date,
                                                  student.teacher.penalty)

        page_count = 0
        for day, times in dict_lessons.items():
            if not times:
                page_count = day
                break

        page_now = state_dict['page']
        print(page_now, page_count)
        if page_now + 1 < page_count:
            return {'dict_lessons': dict_lessons,
                    'student': student,
                    'week_date_str': week_date_str,
                    'page': page_now}
        return False


class IsMoveLeftMenu(BaseFilter):
    async def __call__(self, callback: CallbackQuery, state: FSMContext, session: AsyncSession):
        return (await state.get_data())['page'] - 1 >= 1


# Проверяем, что учитель выставил слоты
class IsTeacherDidSlots(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        state_dict = await state.get_data()
        week_date_str = state_dict['week_date']
        week_date = give_date_format_fsm(state_dict['week_date'])
        student = await give_teacher_by_student_id(session,
                                                   callback.from_user.id)
        if student is not None:
            create_slots = (
                await session.execute(
                    select(LessonWeek)
                    .where(
                        and_(LessonWeek.week_date == week_date,
                             LessonWeek.teacher_id == student.teacher_id)
                    )
                )
            ).scalar()
            if create_slots:
                return {'week_date_str': week_date_str,
                        'student': student,
                        'page': state_dict['page']
                        }
        return False


# Проверяем, есть ли свободные слоты
class IsFreeSlots(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        state_dict = await state.get_data()
        week_date = give_date_format_fsm(state_dict['week_date'])
        student = await give_teacher_by_student_id(session,
                                                   callback.from_user.id)

        lessons_busy = await give_all_busy_time_intervals(session,
                                                          student.teacher_id,
                                                          week_date)

        lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
        dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date,
                                                  student.teacher.penalty)

        if sum(bool(value) for value in dict_lessons.values()) != 0:
            return {'dict_lessons': dict_lessons}
        return False


class IsStudentChooseSlots(BaseFilter):

    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        state_dict = await state.get_data()
        week_date = give_date_format_fsm(state_dict['week_date'])
        all_lessons_for_day = (await give_all_lessons_for_day(session,
                                                week_date,
                                                callback.from_user.id)
                                                ).all()
        if all_lessons_for_day:
            return {'week_date_str': state_dict['week_date'],
                    'page': state_dict['page'],
                    'all_busy_lessons': all_lessons_for_day}
                    
        return False
        


class IsMoveRightRemoveMenu(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext):
        state_dict = await state.get_data()
        week_date_str = state_dict['week_date']
        week_date = give_date_format_fsm(week_date_str)

        all_busy_lessons = await give_all_lessons_for_day(session,
                                                          week_date,
                                                          callback.from_user.id)
        dict_for_6_lessons = create_delete_time_student(all_busy_lessons)

        day_page = 1
        for day, value in dict_for_6_lessons.items():
            if not value:
                day_page = day
                break

        if state_dict['page'] + 1 < day_page:
            return {
                    'week_date_str': week_date_str,
                    'dict_for_6_lessons': dict_for_6_lessons,
                    'page': state_dict['page']}
        return False


class IsLessonsInChoseDay(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession, state: FSMContext,
                       callback_data: ShowDaysOfScheduleCallbackFactory):
        week_date = give_date_format_fsm(callback_data.week_date)

        all_lessons_for_day_not_ordered = (
            await give_all_lessons_for_day(session,
                                            week_date,
                                            callback.from_user.id
                                            )
                                        ).all()

        if all_lessons_for_day_not_ordered:
            return {'all_lessons_for_day_not_ordered': all_lessons_for_day_not_ordered,
                    'week_date': week_date}
        return F


# Проверка на то, что время удаления слота еще не истекло! - Иначе удалить никак!!
class IsTimeNotExpired(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession,
                       callback_data: DeleteFieldCallbackFactory):
        student = (await session.execute(
            select(Student)
            .where(Student.student_id == callback.from_user.id)
            .options(selectinload(Student.teacher))
        )
                   ).scalar()

        if student.teacher.penalty == 0:
            return True
        
        week_date = give_date_format_fsm(callback_data.week_date)
        penalty_delta = timedelta(hours=student.teacher.penalty)
        lesson_start = give_time_format_fsm(callback_data.lesson_start)
        choose_datetime = datetime(year=week_date.year,
                                   month=week_date.month,
                                   day=week_date.day,
                                   hour=lesson_start.hour,
                                   minute=lesson_start.minute)
        print('now: ', datetime.now(),'will: ', choose_datetime - penalty_delta)
        return datetime.now() < choose_datetime - penalty_delta


# Фильтр отвечает за то, установил учитель систему пенальти или нет (подгружаем teacher для ученика)
class IsTeacherDidSystemPenalties(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession):
        student = await session.execute(
            select(Student)
            .where(
                Student.student_id == callback.from_user.id
            )
            .options(selectinload(Student.teacher))
        )
        return student.scalar().teacher.penalty


# Проверяем, есть ли у студента пенальти
class IsStudentHasPenalties(BaseFilter):
    async def __call__(self, callback: CallbackQuery, session: AsyncSession):
        result = await session.execute(
            select(Penalty)
            .where(
                Penalty.student_id == callback.from_user.id
            )
        )
        return result.scalar()
