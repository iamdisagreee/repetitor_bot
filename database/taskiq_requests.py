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

# Получаем список преподавателей, которым надо отправить уведомление, что
# такой-то такой-то ученик не оплатил занятие (список учеников), и те, кому не надо
# async def give_scheduled_payment_verification_teachers(session: AsyncSession):
    # student_ids = (
    #         select(LessonDay.student_id)
    #         .distinct()
    #         .where(
    #             and_(
    #                 LessonDay.status == False,
    #                 LessonDay.week_date <= datetime.now().date()
    #             )
    #         )
    #     )

    # need_sent = (
    #     select(Teacher)
    #     .options(selectinload(
    #         Teacher.students.and_(
    #             Student.student_id.in_(student_ids)
    #             )
    #         )
    #     )
    # )
    # not_need_sent = ( select(Teacher)
    #     .options(selectinload(
    #         Teacher.students.and_(
    #             Student.student_id.in_(student_ids)
    #             )
    #         )
    #     )
    # )

    # result_need = await session.execute(need_sent)
    # result_not_need = await session.execute(not_need_sent)
    #
    # return result.scalars().all()
    # print(result.scalars())
    # for teacher in result.scalars():
    #     print(teacher.name)
    #     for student in teacher.students:
    #         print(student.name)
    # return result.scalars()

#Получаем всю статистику за день
async def give_information_for_day(session: AsyncSession,
                                   teacher_id: int):
    subquery = (
        select(LessonDay)
        .where(LessonDay.week_date == datetime.now().date())
        .order_by(LessonDay.lesson_start)
        .subquery()
    )
    result = await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
        .options(
            selectinload(Teacher.students)
            .selectinload(
                Student.lessons.and_(LessonDay.week_date == datetime.now().date()))
        )
        # .join(LessonDay, LessonDay.teacher_id == Teacher.teacher_id)
        # .order_by(LessonDay.lesson_start)
        # .join(Student)  # Присоединяем Student
        # .join(subquery, Student.lessons)  # Присоединяем подзапрос
    )
    # result = await session.execute(
    #     select(Teacher)
    #     .join(LessonDay, LessonDay.teacher_id == Teacher.teacher_id)
    #     .where(
    #         and_(Teacher.teacher_id == teacher_id,
    #              LessonDay.week_date == date.today()
    #              )
    #     )
    #     .options(selectinload(Teacher.students)
    #              .selectinload(Student.lessons)
    #              )
    #     .filter(LessonDay.week_date == datetime.now().date())
    #     .order_by(LessonDay.lesson_start)
    # )

    teacher = result.scalar()
    return teacher
    #
    # for teacher in teachers:
    #     print('Учитель:', teacher.name, teacher.surname)
    #     print('Ученики:')
    #     for student in teacher.students:
    #         print(student.name, student.surname)
    #         print('Занятия:')
    #         for lesson in student.lessons:
    #             print(f'{lesson.lesson_start}-{lesson.lesson_finished}')

