from collections import defaultdict
from datetime import datetime, date, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from bot.database import Student, LessonDay, Teacher


# Получаем список учеников, которые не оплатили занятие до 23:50 текущего дня
async def give_scheduled_payment_verification_students(session: AsyncSession):
        stmt = (
            select(LessonDay.student_id)
            .distinct()
            .where(
                and_(
                    LessonDay.status == False,
                    LessonDay.week_date == datetime.now().date()
                )
            )
        )

        list_not_paid_students = await session.execute(stmt)

        return list_not_paid_students.scalars().all()

#Получаем всю статистику за день
async def give_information_for_day(session: AsyncSession,
                                   teacher_id: int):
    result = await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
        .options(
            selectinload(Teacher.students)
            .selectinload(
                Student.lessons.and_(LessonDay.week_date == datetime.now().date()))
        )
    )
    teacher = result.scalar()
    return teacher

#Получаем информацию об ученике по его id
async def give_student_by_student_id(session: AsyncSession,
                                     student_id: int):
    student = await session.execute(
        select(Student)
        .where(Student.student_id == student_id)
    )

    return student.scalar()

#Информация для каждого student_id. {student_id: {week_date1: [12:30, 13:30, ...], week_date2: [..],}, student_id2: ...}
async def give_lessons_for_day_students(session: AsyncSession):

    lessons = (await session.execute(
        select(LessonDay)
        .where(LessonDay.week_date >= date.today())
        .order_by(LessonDay.lesson_start, LessonDay.week_date)
        .options(selectinload(LessonDay.student))
    )).scalars().all()

    group_dict = defaultdict(lambda: defaultdict(list))

    for lesson in lessons:
        if lesson.student.until_hour_notification is None:
            continue
        group_dict[lesson.student_id][lesson.week_date].append(lesson)

    return group_dict

#Информация для каждого teacher_id.
# {teacher_id1: {student_id1: {week_date1: [12:30, 13:30, ...],
#                             week_date2: [13:30, 14:00],
#                             week_date3: [...]
#                             }
#               student_id2: {week_date2: [...],}
#  teacher_id2: {student_id1: ...,
#                student_id2: ...
#               }
async def give_lessons_for_day_teacher(session: AsyncSession):
    lessons = (await session.execute(
        select(LessonDay)
        .where(LessonDay.week_date >= date.today())
        .order_by(LessonDay.lesson_start, LessonDay.week_date)
        .options(selectinload(LessonDay.student).selectinload(Student.teacher))
    )).scalars().all()

    group_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for lesson in lessons:
        if lesson.student.teacher.until_hour_notification is None:
            continue
        group_dict[lesson.student.teacher.teacher_id][lesson.student_id][lesson.week_date].append(lesson)

    return group_dict


# Меняем статус отправки у студента на "2" после отправки сообщения
async def change_student_mailing_status(session: AsyncSession,
                                        status: int,
                                        student_id: int,
                                        week_date: date,
                                        lesson_start: time):
    lesson_day = (await session.execute(
        select(LessonDay)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start == lesson_start
            )
        )
    )).scalar()
    lesson_day.student_mailing_status = status

    await session.commit()


# Меняем статус отправки у учителя на "2" после отправки сообщения
async def change_teacher_mailing_status(session: AsyncSession,
                                        status: int,
                                        teacher_id: int,
                                        week_date: date,
                                        lesson_start: time):
    lesson_day = (await session.execute(
        select(LessonDay)
        .where(
            and_(
                LessonDay.teacher_id == teacher_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start == lesson_start
            )
        )
    )).scalar()
    lesson_day.teacher_mailing_status = status

    await session.commit()