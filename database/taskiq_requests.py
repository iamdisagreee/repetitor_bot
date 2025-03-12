from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database import Student, LessonDay, Teacher


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

# Получаем список преподавателей, которым надо отправить уведомление, что
# такой-то такой-то ученик не оплатил занятие (список учеников)
async def give_scheduled_payment_verification_teachers(session: AsyncSession):
    student_ids = (
            select(LessonDay.student_id)
            .distinct()
            .where(
                and_(
                    LessonDay.status == False,
                    LessonDay.week_date <= datetime.now().date()
                )
            )
        )

    stmt = (
        select(Teacher)
        .options(selectinload(
            Teacher.students.and_(
                Student.student_id.in_(student_ids)
                )
            )
        )
    )

    result = await session.execute(stmt)
    return result.scalars().all()
    # print(result.scalars())
    # for teacher in result.scalars():
    #     print(teacher.name)
    #     for student in teacher.students:
    #         print(student.name)
    # return result.scalars()

#Получаем всю статистику за день
async def give_information_for_day(session: AsyncSession):
    # result = await session.execute(
    #     select(Teacher)
    # )
    # return result.scalars()
    result = await session.execute(
        select(Teacher)
        .options(
            selectinload(Teacher.students)
            .selectinload(
                Student.lessons.and_(LessonDay.week_date == datetime.now().date()))
        )
    )

    teachers = result.scalars()
    return teachers
    #
    # for teacher in teachers:
    #     print('Учитель:', teacher.name, teacher.surname)
    #     print('Ученики:')
    #     for student in teacher.students:
    #         print(student.name, student.surname)
    #         print('Занятия:')
    #         for lesson in student.lessons:
    #             print(f'{lesson.lesson_start}-{lesson.lesson_finished}')

