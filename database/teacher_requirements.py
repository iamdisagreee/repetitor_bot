from datetime import datetime, date, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database import LessonDay
from database.models.lesson_week import LessonWeek
from database.models.teacher import Teacher


# Добавляем репетитора в базу данных
async def command_add_teacher(session: AsyncSession,
                              teacher_id: int,
                              name: str,
                              surname: str):
    result = await session.execute(select(Teacher)
                                   .where(Teacher.teacher_id == teacher_id))

    if result.scalar() is None:
        teacher = Teacher(teacher_id=teacher_id,
                          name=name,
                          surname=surname)

        session.add(teacher)
        await session.commit()


# Добавляем день, в котором будет хранится информация о занятиях
async def command_add_lesson_week(session: AsyncSession,
                                  teacher_id: int,
                                  week_date: date,
                                  work_start: time,
                                  work_end: time):
    lessons_week = LessonWeek(teacher_id=teacher_id,
                              week_date=week_date,
                              work_start=work_start,
                              work_end=work_end)

    session.add(lessons_week)
    await session.commit()


# Получаем все данные о текущем дне (все его окошки для занятий)
async def give_installed_lessons_week(session: AsyncSession,
                                      teacher_id: int,
                                      week_date: date):
    res_time = await session.execute(
        select(LessonWeek)
        .where(
            and_(
                LessonWeek.teacher_id == teacher_id,
                LessonWeek.week_date == week_date
            )
        )
        .order_by(LessonWeek.work_start)
    )

    return res_time.scalars()


async def delete_week_day(session: AsyncSession,
                          week_id: int):
    stmt = select(LessonWeek).where(LessonWeek.week_id == week_id)

    res_found = (await session.execute(stmt)).scalar()

    await session.delete(res_found)
    await session.commit()


async def give_all_lessons_day_by_week_day(session: AsyncSession,
                                           teacher_id: int,
                                           week_date: date):
    stmt = (
        select(LessonWeek)
        .where(
            and_(
                LessonWeek.teacher_id == teacher_id,
                LessonWeek.week_date == week_date
            )
        )
        .order_by(LessonWeek.work_start)
        .options(selectinload(LessonWeek.lessons))
    )

    result = await session.execute(stmt)
    sort_lessons = []
    for week_lesson in result.scalars():
        #print('FFFF', week_lesson.week_date, week_lesson.work_start, week_lesson.work_end)
        for lesson in week_lesson.lessons:
            continue
           # print(lesson.lesson_start, lesson.lesson_finished)

