from datetime import datetime, date, time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from database import LessonDay, Student, AccessStudent
from database.models.lesson_week import LessonWeek
from database.models.teacher import Teacher


# Добавляем репетитора в базу данных
async def command_add_teacher(session: AsyncSession,
                              teacher_id: int,
                              name: str,
                              surname: str,
                              phone: str,
                              bank: str,
                              penalty: int):
    teacher = Teacher(teacher_id=teacher_id,
                      name=name,
                      surname=surname,
                      phone=phone,
                      bank=bank,
                      penalty=penalty)

    await session.merge(teacher)
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
                          week_id: UUID):
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

    return result.scalars()

    # for week_lesson in result.scalars():
    #     sorted_lessons = sorted(week_lesson.lessons, key=lambda x: x.lesson_start)
    #     print('FFFF', week_lesson.week_date, week_lesson.work_start, week_lesson.work_end)
    #     for lesson in sorted_lessons:
    #         print(lesson.lesson_start, lesson.lesson_finished)
    # exit()


async def give_student_by_student_id(session: AsyncSession,
                                     student_id: int):
    result = await session.execute(select(Student)
                                   .where(Student.student_id == student_id))

    return result.scalar()


async def change_status_pay_student(session: AsyncSession,
                                    student_id: int,
                                    week_date: date,
                                    lesson_on: time,
                                    lesson_off: time):
    lesson_days = await session.execute(
        select(LessonDay)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
                LessonDay.lesson_finished <= lesson_off
            )
        )
        .order_by(LessonDay.lesson_start)
    )

    list_lessons = {}
    for lesson_day in lesson_days.scalars():
        # Проверяем случай, когда занятие оплачено, но добавился новый промежуток
        list_lessons[lesson_day.status] = lesson_day
    if sum(list_lessons.keys()) != len(list_lessons.keys()) and sum(list_lessons.keys()) > 0:
        for lesson_day_u in list_lessons.values():
            lesson_day_u.status = False
    else:
        for lesson_day_u in list_lessons.values():
            if lesson_day_u.status:
                lesson_day_u.status = False
            else:
                lesson_day_u.status = True

    await session.commit()


async def give_information_of_one_lesson(session: AsyncSession,
                                         teacher_id: int,
                                         week_date: date,
                                         lesson_on: time,
                                         lesson_off: time):
    stmt = (
        select(LessonDay)
        .where(
            and_(
                LessonDay.teacher_id == teacher_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
                LessonDay.lesson_finished <= lesson_off
            )
        )
        .options(selectinload(LessonDay.student))
    )

    result = await session.execute(stmt)

    return result.scalar()


async def delete_lesson(session: AsyncSession,
                        week_date: date,
                        lesson_on: time,
                        lesson_off: time):
    delete_lessons = await session.execute(
        select(LessonDay)
        .where(
            and_(
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
                LessonDay.lesson_finished <= lesson_off
            )
        )
    )

    for lesson in delete_lessons.scalars():
        await session.delete(lesson)
    await session.commit()


async def delete_teacher_profile(session: AsyncSession,
                                 teacher_id: int):
    profile = await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )

    await session.delete(profile.scalar())
    await session.commit()


async def give_student_id_by_teacher_id(session: AsyncSession,
                                        teacher_id,
                                        week_date,
                                        lesson_on):
    student_id = await session.execute(
        select(LessonDay.student_id)
        .where(
            and_(
                LessonDay.week_date == week_date,
                LessonDay.teacher_id == teacher_id,
                LessonDay.lesson_start == lesson_on
            )
        )
    )

    return student_id.scalar()


async def give_penalty_by_teacher_id(session: AsyncSession,
                                     teacher_id: int):
    result = await session.execute(
        select(Teacher.penalty)
        .where(Teacher.teacher_id == teacher_id)
    )

    return result.scalar()


# Список всех учеников для репетитора
async def give_all_students_by_teacher(session: AsyncSession,
                                       teacher_id: int):
    result = await session.execute(
        select(Student)
        .where(Student.teacher_id == teacher_id)
        .order_by(Student.surname)
        .options(selectinload(Student.access))
    )

    return result.scalars()


# Меняем статус ученика на обратный '🔒' -> '🔑'/ '🔑' -> '🔒'
async def change_status_entry_student(session: AsyncSession,
                                      student_id: int):
    student = (
        await session.execute(
            select(AccessStudent)
            .where(AccessStudent.student_id == student_id)
        )
    ).scalar()

    student.status = not student.status
    await session.commit()


# Получаем статус ученика
async def give_status_entry_student(session: AsyncSession,
                                    student_id: int):
    student_status = (
        await session.execute(
            select(AccessStudent.status)
            .where(AccessStudent.student_id == student_id)
        )
    ).scalar()
    print(student_status)
    return student_status


# Добавляем ученика в базу данных, то есть даем ему возможность начать регистрацию

async def add_student_id_in_database(session: AsyncSession,
                                     student_id: int):
    accessStudent = AccessStudent(student_id=student_id)

    session.add(accessStudent)
    await session.commit()


async def delete_student_id_in_database(session: AsyncSession,
                                        student_id: int):
    access_student = await session.execute(
        select(AccessStudent)
        .where(AccessStudent.student_id == student_id)
    )

    await session.delete(access_student.scalar())
    await session.commit()


async def give_all_students_by_teacher_penalties(session: AsyncSession,
                                                 teacher_id: int):
    result = await session.execute(
        select(Student)
        .where(Student.teacher_id == teacher_id)
        .options(selectinload(Student.penalties))
    )

    return result.scalars()


# Получаем студента со всей вытекающей по его teacher_id, week_date, lesson_on
async def give_student_by_teacher_id(session: AsyncSession,
                                     teacher_id,
                                     week_date,
                                     lesson_on):
    student_id = (await session.execute(
        select(LessonDay.student_id)
        .where(
            and_(
                LessonDay.week_date == week_date,
                LessonDay.teacher_id == teacher_id,
                LessonDay.lesson_start == lesson_on
            )
        )
    )).scalar()

    student = await session.execute(
        select(Student)
        .where(Student.student_id == student_id)
        .options(
            selectinload(Student.access),
            selectinload(Student.penalties)
        )
    )

    return student.scalar()


# Удаляем все занятия ученика, если его забанили
async def delete_all_lessons_student(session: AsyncSession,
                                     student_id: int):
    result = await session.execute(
        select(LessonDay)
        .where(LessonDay.student_id == student_id)
    )

    for student in result.scalars():
        await session.delete(student)
    await session.commit()
