from datetime import datetime, date, time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from database import LessonDay, Student, AccessStudent, Debtor
from database.models import Penalty
from database.models.lesson_week import LessonWeek
from database.models.teacher import Teacher


# Добавляем репетитора в базу данных
async def command_add_teacher(session: AsyncSession,
                              teacher_id: int,
                              name: str,
                              surname: str,
                              phone: str,
                              bank: str,
                              penalty: int,
                              until_hour_notification: int = None,
                              until_minute_notification: int = None,
                              daily_schedule_mailing_time: time = None,
                              daily_report_mailing_time: time = None,
                              days_cancellation_notification: int = None,
                              ):
    teacher_now = (await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )).scalar()

    if teacher_now is not None:
        until_hour_notification = teacher_now.until_hour_notification
        until_minute_notification = teacher_now.until_minute_notification
        daily_schedule_mailing_time = teacher_now.daily_schedule_mailing_time
        daily_report_mailing_time = teacher_now.daily_report_mailing_time
        days_cancellation_notification = teacher_now.days_cancellation_notification

    teacher = Teacher(teacher_id=teacher_id,
                      name=name,
                      surname=surname,
                      phone=phone,
                      bank=bank,
                      penalty=penalty,
                      until_hour_notification=until_hour_notification,
                      until_minute_notification=until_minute_notification,
                      daily_schedule_mailing_time=daily_schedule_mailing_time,
                      daily_report_mailing_time=daily_report_mailing_time,
                      days_cancellation_notification=days_cancellation_notification)

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
    now = datetime.now()
    cur_time = now.time()
    cur_date = now.date()
    if cur_date == week_date:
        res_time = await session.execute(
            select(LessonWeek)
            .where(
                and_(
                    LessonWeek.teacher_id == teacher_id,
                    LessonWeek.week_date == week_date,
                    LessonWeek.work_end > cur_time
                )
            )
            .order_by(LessonWeek.work_start)
        )
    else:
        res_time = await session.execute(
            select(LessonWeek)
            .where(
                and_(
                    LessonWeek.teacher_id == teacher_id,
                    LessonWeek.week_date == week_date,
                )
            )
            .order_by(LessonWeek.work_start)
        )

    return res_time.scalars()


async def give_installed_lessons_week_without_restrictions(
        session: AsyncSession,
        teacher_id: int,
        week_date: date):
    res_time = await session.execute(
        select(LessonWeek)
        .where(
            and_(
                LessonWeek.teacher_id == teacher_id,
                LessonWeek.week_date == week_date,
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


async def give_student_by_student_id(session: AsyncSession,
                                     student_id: int):
    result = await session.execute(select(Student)
                                   .where(Student.student_id == student_id))

    return result.scalar()


async def give_status_pay_student(session: AsyncSession,
                                  student_id: int,
                                  week_date: date,
                                  lesson_on: time,
                                  lesson_off: time
                                  ):
    lesson_days = await session.execute(
        select(LessonDay.status)
        .where(
            and_(
                LessonDay.student_id == student_id,
                LessonDay.week_date == week_date,
                LessonDay.lesson_start >= lesson_on,
            )
        )
        # .order_by(LessonDay.lesson_start)
    )

    return lesson_days.scalar()


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
    status = False
    list_lessons = {}
    for lesson_day in lesson_days.scalars():
        list_lessons[lesson_day] = lesson_day.status

    if sum(list_lessons.values()) != len(list_lessons) and sum(list_lessons.values()) > 0:
        for lesson_day_u in list_lessons.keys():
            lesson_day_u.status = False
    else:
        for lesson_day_u in list_lessons.keys():
            if status or not lesson_day_u.status:
                status = True
            lesson_day_u.status = not lesson_day_u.status
    await session.commit()

    return status


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


async def give_teacher_profile_by_teacher_id(session: AsyncSession,
                                             teacher_id):
    profile = await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )

    return profile.scalar()


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


# Получаем статус доступа ученика
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
        .where(
            and_(
                Student.teacher_id == teacher_id,
                Student.penalties != None
            )
        )
        .options(selectinload(Student.penalties))
        .order_by(Student.surname)
    )

    return result.scalars()


# Получаем студента со всей вытекающей по его teacher_id, week_date, lesson_on
async def give_student_by_teacher_id(session: AsyncSession,
                                     teacher_id,
                                     week_date,
                                     lesson_on):
    student = await session.execute(
        select(Student)
        .join(LessonDay, Student.student_id ==
              LessonDay.student_id)
        .where(
            and_(
                LessonDay.week_date == week_date,
                LessonDay.teacher_id == teacher_id,
                LessonDay.lesson_start == lesson_on
            )
        )
        .options(
            selectinload(Student.access),
            selectinload(Student.penalties),
            selectinload(Student.teacher),
        )
    )
    return student.scalar()


async def give_student_by_teacher_id_debtors(session: AsyncSession,
                                             teacher_id: int,
                                             week_date: date,
                                             lesson_on: time):
    student = await session.execute(
        select(Student)
        .join(LessonDay, Student.student_id == LessonDay.student_id)
        .where(
            and_(
                LessonDay.week_date == week_date,
                LessonDay.teacher_id == teacher_id,
                LessonDay.lesson_start == lesson_on
            )
        )
    )
    return student.scalar()

# Удаляем все занятия ученика
async def delete_all_lessons_student(session: AsyncSession,
                                     student_id: int):
    to_delete_lesson_day = (delete(LessonDay)
                            .where(Student.student_id == student_id))
    await session.execute(to_delete_lesson_day)
    await session.commit()


async def delete_all_penalties_student(session: AsyncSession,
                                       student_id: int):
    to_delete_penalty = (delete(Penalty)
                         .where(Student.student_id == student_id))

    await session.execute(to_delete_penalty)
    await session.commit()


async def add_penalty_to_student(session: AsyncSession,
                                 student_id: int,
                                 week_date,
                                 lesson_on,
                                 lesson_off):
    penalty = Penalty(student_id=student_id,
                      week_date=week_date,
                      lesson_on=lesson_on,
                      lesson_off=lesson_off)

    session.add(penalty)
    await session.commit()


async def delete_penalty_of_student(session: AsyncSession,
                                    student_id: int):
    stmt = delete(Penalty).where(Penalty.student_id == student_id)

    await session.execute(stmt)
    await session.commit()


async def give_list_debtors(session: AsyncSession,
                            teacher_id: int):
    stmt = (
        select(Debtor)
        .where(Debtor.teacher_id == teacher_id)
        .order_by(Debtor.week_date, Debtor.lesson_on)
        .options(selectinload(Debtor.student))
    )
    list_debtors = await session.execute(stmt)
    return list_debtors.scalars().all()


async def remove_debtor_from_list(session: AsyncSession,
                                  debtor_id: UUID):
    await session.execute(
        delete(Debtor)
        .where(Debtor.debtor_id == debtor_id)
    )
    await session.commit()

async def update_until_time_notification_teacher(session: AsyncSession,
                                                 teacher_id: int,
                                                 until_hour_notification,
                                                 until_minute_notification):
    teacher = (await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )).scalar()
    teacher.until_hour_notification = until_hour_notification
    teacher.until_minute_notification = until_minute_notification
    await session.commit()

async def update_daily_schedule_mailing_teacher(session: AsyncSession,
                                                teacher_id: int,
                                                daily_schedule_mailing_time: time
                                                ):
    teacher = (await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )).scalar()
    teacher.daily_schedule_mailing_time = daily_schedule_mailing_time
    await session.commit()

async def update_daily_report_mailing_teacher(session: AsyncSession,
                                                teacher_id: int,
                                                daily_report_mailing_time: time
                                                ):
    teacher = (await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )).scalar()
    teacher.daily_report_mailing_time = daily_report_mailing_time
    await session.commit()

async def update_days_cancellation_teacher(session: AsyncSession,
                                           teacher_id: int,
                                            days_cancellation_notification: int):
    teacher = (await session.execute(
        select(Teacher)
        .where(Teacher.teacher_id == teacher_id)
    )).scalar()
    teacher.days_cancellation_notification = days_cancellation_notification
    await session.commit()