from datetime import datetime, date, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, update
from sqlalchemy.orm import selectinload

from bot.database import Student, LessonDay, Debtor
from bot.database.models.penalty import Penalty
from bot.database.models.lesson_week import LessonWeek
from bot.database.models.teacher import Teacher


# Получаем список всех учителей
async def command_get_all_teachers(session: AsyncSession):
    result = await session.execute(
        select(Teacher)
        .order_by(Teacher.surname)
    )

    return result.scalars()


# Добавляем ученика
async def command_add_students(session: AsyncSession,
                               student_id,
                               name,
                               surname,
                               city,
                               place_study,
                               subject,
                               teacher_id: str,
                               price,
                               until_hour_notification=None,
                               until_minute_notification=None,
                               class_learning=None,
                               course_learning=None,
                               ):
    student_cur = (await session.execute(
        select(Student)
        .where(Student.student_id == student_id)
    )).scalar()

    if student_cur is not None:
        until_hour_notification = student_cur.until_hour_notification
        until_minute_notification = student_cur.until_minute_notification

    student = Student(student_id=student_id,
                      name=name,
                      surname=surname,
                      city=city,
                      place_study=place_study,
                      class_learning=int(class_learning) if class_learning else class_learning,
                      course_learning=int(course_learning) if course_learning else course_learning,
                      subject=subject,
                      teacher_id=int(teacher_id),
                      price=int(price),
                      until_hour_notification=until_hour_notification,
                      until_minute_notification=until_minute_notification
                      )
    await session.merge(student)
    await session.commit()


async def give_lessons_week_for_day(session: AsyncSession,
                                    week_date: date,
                                    teacher_id: int):
    stmt = (
        select(LessonWeek)
        .where(
            and_(LessonWeek.week_date == week_date,
                 LessonWeek.teacher_id == teacher_id)
        )
        .order_by(LessonWeek.work_start)
    )

    lessons_week_for_day = await session.execute(stmt)

    return lessons_week_for_day.scalars()


# Получаем список существующих записей на заданный день
async def give_all_busy_time_intervals(session: AsyncSession,
                                       teacher_id: int,
                                       week_date: date):
    result = await session.execute(
        select(LessonDay)
        .where(
            and_(
                LessonDay.week_date == week_date,
                LessonDay.teacher_id == teacher_id
            )
        )
    )

    return result.scalars()


async def add_lesson_day(session: AsyncSession,
                         week_date: time,
                         week_id: int,
                         teacher_id: int,
                         student_id: int,
                         lesson_start: time,
                         lesson_finished: time):
    lesson_day = LessonDay(
        week_date=week_date,
        week_id=week_id,
        teacher_id=teacher_id,
        student_id=student_id,
        lesson_start=lesson_start,
        lesson_finished=lesson_finished,
    )

    session.add(lesson_day)
    await session.commit()


async def give_teacher_by_student_id(session: AsyncSession,
                                     student_id: int):
    student = await session.execute(
        select(Student)
        .where(Student.student_id == student_id)
        .options(selectinload(Student.teacher)))

    return student.scalar()


async def give_week_id_by_teacher_id(session: AsyncSession,
                                     teacher_id: int,
                                     week_date: time,
                                     lesson_start: time,
                                     lesson_finished: time):
    week_id = await session.execute(
        select(LessonWeek.week_id)
        .where(
            and_(LessonWeek.teacher_id == teacher_id,
                 LessonWeek.week_date == week_date,
                 LessonWeek.work_start <= lesson_start,
                 LessonWeek.work_end >= lesson_finished)
        )
    )

    return week_id.scalar()


async def give_all_lessons_for_day(session: AsyncSession,
                                   week_date: date,
                                   student_id: int):
    now = datetime.now()

    all_lessons_for_day = await session.execute(
        select(LessonDay)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
            )
        ).order_by(LessonDay.lesson_start)
    )

    return all_lessons_for_day.scalars()


async def remove_lesson_day(session: AsyncSession,
                            student_id: int,
                            week_date: time,
                            lesson_start: time,
                            lesson_finished: time):
    delete_lesson = (await session.execute(
        select(LessonDay)
        .where(
            and_(LessonDay.lesson_start == lesson_start,
                 LessonDay.lesson_finished == lesson_finished,
                 LessonDay.student_id == student_id,
                 LessonDay.week_date == week_date)
        )
    )
                     ).scalar()

    await session.delete(delete_lesson)
    await session.commit()


async def give_all_information_teacher(session: AsyncSession,
                                       teacher_id: int):
    stmt = (
        select(Teacher).where(Teacher.teacher_id == teacher_id)
    )

    result = await session.execute(stmt)

    return result.scalar()


# Все интервалы, которые лежат в уроке
async def give_information_of_lesson(session: AsyncSession,
                                     student_id: int,
                                     week_date: date,
                                     lesson_on: time,
                                     lesson_off: time):
    stmt = (
        select(LessonDay)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
                LessonDay.lesson_finished <= lesson_off
            )
        )
    )
    result = await session.execute(stmt)

    return result.scalars()

async def change_formed_status_lessons_day(session: AsyncSession,
                                           student_id: int,
                                           week_date: date,
                                           lesson_on: time,
                                           lesson_off: time):
    await session.execute(
        update(LessonDay)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
                LessonDay.lesson_finished <= lesson_off
            )
        )
        .values(is_formed=True)
    )

    await session.commit()

async def delete_student_profile(session: AsyncSession,
                                 student_id: int):
    await session.execute(delete(Student)
                                    .where(Student.student_id == student_id))
    await session.commit()


async def give_students_penalty(session: AsyncSession,
                                student_id: int):
    student_penalties = await session.execute(
        select(Penalty)
        .where(Penalty.student_id == student_id)
    )

    return student_penalties.scalars().all()


# Удаляем все интервалы из переданного списка
async def delete_gap_lessons_by_student(session: AsyncSession,
                                        student_id: int,
                                        week_date: date,
                                        lesson_on: time,
                                        lesson_off: time):
    stmt = (
        delete(LessonDay)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
                LessonDay.lesson_finished <= lesson_off
            )
        )
    )

    await session.execute(stmt)


async def give_all_debts_student(session: AsyncSession,
                                 student_id: int):
    list_debts = await session.execute(
        select(Debtor)
        .where(Debtor.student_id == student_id)
    )

    return list_debts.scalars().all()

async def add_until_time_notification(session: AsyncSession,
                                      student_id: int,
                                      until_hour_notification: int,
                                      until_minute_notification: int):
    student = (await session.execute(
        select(Student)
        .where(Student.student_id == student_id)
    )).scalar()

    student.until_hour_notification = until_hour_notification
    student.until_minute_notification = until_minute_notification
    await session.commit()

