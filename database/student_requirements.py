from datetime import datetime, date, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database import Student, LessonDay
from database.models.lesson_week import LessonWeek
from database.models.teacher import Teacher


# Получаем список всех учителей
async def command_get_all_teachers(session: AsyncSession):
    result = await session.execute(select(Teacher))

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
                               class_learning=None,
                               course_learning=None,
                               ):
    student = Student(student_id=student_id,
                      name=name,
                      surname=surname,
                      city=city,
                      place_study=place_study,
                      class_learning=int(class_learning) if class_learning else class_learning,
                      course_learning=int(course_learning) if course_learning else course_learning,
                      subject=subject,
                      teacher_id=int(teacher_id),
                      price=int(price)
                      )

    session.add(student)
    await session.commit()


async def give_lessons_week_for_day(session: AsyncSession,
                                    week_date: date):
    stmt = (select(LessonWeek)
            .where(LessonWeek.week_date == week_date))

    lessons_week_for_day = await session.execute(stmt)

    return lessons_week_for_day.scalars()


async def add_lesson_day(session: AsyncSession,
                         week_date: time,
                         week_id: int,
                         teacher_id: int,
                         student_id: int,
                         lesson_start: time,
                         lesson_end: time):
    lesson_day = LessonDay(
        wee_date=week_date,
        week_id=week_id,
        teacher_id=teacher_id,
        student_id=student_id,
        lesson_start=lesson_start,
        lesson_end=lesson_end,
    )

    session.add(lesson_day)
    await session.commit()
