from datetime import datetime, date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, not_
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