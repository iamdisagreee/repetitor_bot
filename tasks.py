import asyncio
from collections import defaultdict
from datetime import datetime, date, timedelta, time, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from broker import worker, scheduler_storage
from callback_factory.student_factories import InformationLessonCallbackFactory
from database import AccessStudent, Teacher, Debtor
from taskiq import Context, TaskiqDepends

from sqlalchemy import select

from database.taskiq_requests import give_scheduled_payment_verification_students, \
    give_information_for_day, give_student_by_student_id, give_lessons_for_day_students, give_lessons_for_day_teacher, \
    change_student_mailing_status, change_teacher_mailing_status
from database.teacher_requests import give_all_lessons_day_by_week_day
from keyboards.taskiq_kb import create_confirmation_day_teacher_kb, create_confirmation_pay_student_kb, \
    create_notice_lesson_certain_time_student_ok, create_notice_lesson_certain_time_teacher_ok
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from services.services import NUMERIC_DATE, give_date_format_fsm, show_intermediate_information_lesson_day_status, \
    give_time_format_fsm, give_week_day_by_week_date
from services.services_taskiq import give_data_config_teacher, give_everyday_schedule, create_schedule_like_text, \
    check_is_30_minutes_between, create_scheduled_task, change_to_specified_time, \
    give_correct_time_schedule_before_lesson, delete_unnecessary_tasks_teacher, give_dictionary_tasks_teacher, \
    delete_unnecessary_tasks_student, give_dictionary_tasks_student


# Ежедневная рассылка для преподавателя и его учеников-должников
@worker.task(task_name='daily_report_mailing_teacher')
async def daily_newsletter_teacher(teacher_id: int,
                                   context: Context = TaskiqDepends(),
                                   bot: Bot = TaskiqDepends()):
    async with context.state.session_pool() as session:
        teacher = await give_information_for_day(session, teacher_id)

    if teacher.daily_report_mailing_time is None:
        return

    result_debtors, general_information = give_data_config_teacher(teacher)
    text = ''
    for lesson in result_debtors:
        text += f" - {lesson['student_name']} {lesson['student_surname']} {int(lesson['amount_money'])}р." \
                f"{lesson['lesson_on'].strftime('%H:%M')}-{lesson['lesson_off'].strftime('%H:%M')}\n"
    await bot.send_message(chat_id=teacher_id,
                           text=LEXICON_TASKIQ['info_non_payment_teacher']
                           .format(datetime.now().strftime("%d.%m"), give_week_day_by_week_date(date.today()),
                                   f"{general_information['amount_time'] // 3600} ч."
                                   f" {general_information['amount_time'] // 60 % 60} мин.",
                                   int(general_information['amount_money_yes']),
                                   int(general_information['amount_money_no']),
                                   text),
                           reply_markup=create_confirmation_day_teacher_kb()
                           )
    print('Сообщение отправлено преподавателю!')
    # Добавляем учеников в таблицу должников
    async with context.state.session_pool() as session:
        for lesson in result_debtors:
            debtor = Debtor(
                teacher_id=teacher_id,
                student_id=lesson['student_id'],
                week_date=date.today(),
                lesson_on=lesson['lesson_on'],
                lesson_off=lesson['lesson_off'],
                amount_money=lesson['amount_money']
            )
            session.add(debtor)
            await session.commit()
    # Начинаем рассылку для учеников (???)
    iter_result_debtors = iter(result_debtors)
    while True:
        try:
            for student in iter_result_debtors:
                try:
                    await bot.send_message(chat_id=student['student_id'],
                                           text=LEXICON_TASKIQ['forget_paid_students']
                                           .format(datetime.now().strftime("%d.%m"),
                                                   give_week_day_by_week_date(date.today()),
                                                   student['lesson_on'].strftime("%H:%M"),
                                                   student['lesson_off'].strftime("%H:%M"),
                                                   student['amount_money']
                                                   )
                                           ,
                                           reply_markup=create_confirmation_pay_student_kb(
                                               str(date.today()),
                                               student['lesson_on'].strftime("%H:%M"),
                                               student['lesson_off'].strftime("%H:%M"),
                                               student['amount_money']
                                           )
                                           )
                except TelegramForbiddenError:
                    pass
            break
        # except TimeoutError:
        #     print("Рассылка закончена")
        #     break
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after))
            continue
    print('Рассылка для учеников окончена!')


# Высылаем расписание каждый день в __переданное время__ для учителя
@worker.task(task_name='daily_schedule_mailing_teacher')
async def activities_day_teacher(teacher_id: int,
                                 context: Context = TaskiqDepends(),
                                 bot: Bot = TaskiqDepends()):
    async with context.state.session_pool() as session:
        teacher = await give_information_for_day(session,
                                                 teacher_id)
    if teacher.daily_schedule_mailing_time is None:
        return

    result_schedule = give_everyday_schedule(teacher)
    text_schedule = create_schedule_like_text(result_schedule)
    await bot.send_message(chat_id=teacher_id, text=LEXICON_TASKIQ['give_everyday_schedule']
                           .format(text_schedule),
                           reply_markup=create_confirmation_day_teacher_kb())

# Уведомление о занятии за какое-то время до начала
@worker.task(task_name='student_mailing_lessons')
async def student_mailing_lessons(context: Context = TaskiqDepends(),
                                  bot: Bot = TaskiqDepends()):
    await scheduler_storage.startup()

    scheduled_tasks = await give_dictionary_tasks_student()

    # print(await scheduler_storage.get_schedules())

    async with context.state.session_pool() as session:
        list_students_id = await give_lessons_for_day_students(session)
        # Смотрим расписание каждого студента по student_id
        # {student_id: {week_date: [12:30, 13:30, ...], week_date: [..],}, student_id2: ...}
        for student_id, dict_week_date in list_students_id.items():

            # {week_date: [12:30, 13:30, ...]}
            for week_date, lessons_day in dict_week_date.items():


                # Проверяем, что таска не удалена. Если удалена,
                # то меняем статус в обе стороны для всех занятий
                await delete_unnecessary_tasks_student(student_id,
                                                        week_date,
                                                        lessons_day,
                                                        scheduled_tasks)

                # print([x.student_mailing_status for x in lessons_day])

                flag_status = False
                scheduled_tasks = await give_dictionary_tasks_student()
                print(scheduled_tasks)
                for index, lesson_day in enumerate(lessons_day):
                    if len(lessons_day) == 1: break
                    if lesson_day.lesson_start in scheduled_tasks[student_id][week_date] or\
                            lesson_day.student_mailing_status == 2:
                        print(f'STUDENT, {lesson_day.lesson_start} уже зареган!')
                        continue
                    static_index = index
                    if  lesson_day.student_mailing_status == 0 and index + 1 < len(lessons_day):
                        for lesson_day_next in lessons_day[static_index + 1:]:
                            if check_is_30_minutes_between(lesson_day.lesson_start,
                                                           lesson_day_next.lesson_start):
                                if lesson_day_next.student_mailing_status == 1:
                                    # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
                                    await scheduler_storage.delete_schedule(
                                        f'b_l_s_{student_id}_{week_date}_{lesson_day_next.lesson_start}')
                                    break
                                else:
                                    break
                            else:
                                break

                    if lesson_day.student_mailing_status == 1:
                        # Если статус равен единице и слева нет соседей, то ставим уведомление
                        if index != 0 and not check_is_30_minutes_between(lessons_day[index-1].lesson_start,
                                                                          lesson_day.lesson_start):
                            flag_status = True

                    only_change = False
                    if not flag_status and index != 0 and \
                        lessons_day[index - 1].student_mailing_status == 1 and \
                            check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                        lessons_day[index].lesson_start):
                        only_change = True

                    if lesson_day.student_mailing_status == 0:
                        lesson_day.student_mailing_status = 1

                    if not only_change or flag_status:
                        # until_hour, until_minute = lesson_day.student.until_hour, lesson_day.until_minute
                        # until_hour, until_minute = 0, 30
                        await create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                                    labels={str(student_id): [lesson_day.lesson_start,
                                                                              lesson_day.week_date]},
                                                    kwargs={'student_id': student_id,
                                                            'lesson_start': lesson_day.lesson_start,
                                                            'week_date': week_date,
                                                            },
                                                    schedule_id=f'b_l_s_{student_id}_{week_date}_'
                                                                f'{lesson_day.lesson_start}',
                                                    until_hour=lesson_day.student.until_hour_notification,
                                                    until_minute=lesson_day.student.until_minute_notification,
                                                    lesson_start=lesson_day.lesson_start,
                                                    week_date=week_date
                                                    )

        await session.commit()
    for x in await scheduler_storage.get_schedules():
        print(x.schedule_id)
    await scheduler_storage.shutdown()


# Уведомление о занятии за __переданное время__ до занятия для ученика
@worker.task(task_name='notice_lesson_certain_time_student')
async def notice_lesson_certain_time_student(student_id: int,
                                             lesson_start: time,
                                             week_date: date,
                                             time_before_lesson,
                                             context: Context = TaskiqDepends(),
                                             bot: Bot = TaskiqDepends()):
    dt_res = datetime(year=week_date.year, month=week_date.month, day=week_date.day,
                      hour=lesson_start.hour, minute=lesson_start.minute)

    await bot.send_message(chat_id=student_id, text=LEXICON_TASKIQ['time_before_lesson_student']
    .format(*time_before_lesson, dt_res.strftime("%m.%d %H:%M")),
                           reply_markup=create_notice_lesson_certain_time_student_ok()
                           )

    # меняем статус - уведомление отправили
    async with context.state.session_pool() as session:
        await change_student_mailing_status(session=session,
                                            status=2,
                                            student_id=student_id,
                                            week_date=week_date,
                                            lesson_start=lesson_start)


# Уведомление о занятии за какое-то время до начала для репетитора
@worker.task(task_name='teacher_mailing_lessons')
async def teacher_mailing_lessons(context: Context = TaskiqDepends(),
                                          bot: Bot = TaskiqDepends()):
    await scheduler_storage.startup()

    #Словарь запланированных задач
    scheduled_tasks = await give_dictionary_tasks_teacher()

    # print(scheduled_tasks)
    # print(await scheduler_storage.get_schedules())

    async with context.state.session_pool() as session:
        list_teachers_id = await give_lessons_for_day_teacher(session)
        # Смотрим расписание каждого студента по student_id
        # for teacher_id, dict_students in list_teachers_id.items():
        #     print(teacher_id)
        #     for student_id, dict_week_date in dict_students.items():
        #         print('  ', student_id)
        #         for week_date, list_time in dict_week_date.items():
        #             print('    ', 'WEEK_DATE', week_date, ' ', list_time)

        for teacher_id, dict_students in list_teachers_id.items():
            for student_id, dict_week_date in dict_students.items():
                for week_date, lessons_day in dict_week_date.items():
                    # Проверяем, что таска не удалена. Если удалена,
                    # то меняем статус в обе стороны для всех занятий
                    # При условии, что есть какие-то задачи
                    await delete_unnecessary_tasks_teacher(teacher_id,
                                                           student_id,
                                                           week_date,
                                                           lessons_day,
                                                           scheduled_tasks)
                    flag_status = False
                    scheduled_tasks = await give_dictionary_tasks_teacher()
                    # print(scheduled_tasks)
                    for index, lesson_day in enumerate(lessons_day):
                        # Тестовый вариант выборки времени
                        if len(lessons_day) == 1: break
                        if lesson_day.lesson_start in scheduled_tasks[teacher_id][student_id][week_date] or \
                                lesson_day.teacher_mailing_status == 2:
                            print(f'TEACHER, {lesson_day.lesson_start} уже зареган!')
                            continue
                        static_index = index

                        if lesson_day.student_mailing_status == 0 and index + 1 < len(lessons_day):
                            for lesson_day_next in lessons_day[static_index + 1:]:
                                if check_is_30_minutes_between(lesson_day.lesson_start,
                                                               lesson_day_next.lesson_start):
                                    if lesson_day_next.teacher_mailing_status == 1:
                                        # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
                                        await scheduler_storage.delete_schedule(
                                            f'b_l_t_{teacher_id}_{week_date}_{lesson_day_next.lesson_start}')
                                        break
                                    else:
                                        break
                                else:
                                    break

                        if lesson_day.student_mailing_status == 1 and index != 0 \
                                and not check_is_30_minutes_between(lessons_day[index-1].lesson_start,
                                                                              lesson_day.lesson_start):
                            flag_status = True


                        only_change = False
                        if not flag_status and index != 0 and \
                                lessons_day[index - 1].student_mailing_status == 1 and \
                                check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                            lessons_day[index].lesson_start):
                            only_change = True

                        if lesson_day.teacher_mailing_status == 0:
                            lesson_day.teacher_mailing_status = 1

                        if not only_change or flag_status:
                            # until_hour, until_minute = 0, 30
                            await create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                                        labels={str(teacher_id): [lesson_day.student_id,
                                                                             lesson_day.lesson_start,
                                                                             lesson_day.week_date]},
                                                        kwargs={'teacher_id': teacher_id,
                                                                'lesson_start': lesson_day.lesson_start,
                                                                'week_date': week_date,
                                                                'student_info': [lesson_day.student.name,
                                                                                lesson_day.student.surname,
                                                                                 lesson_day.student.subject]
                                                                },
                                                        schedule_id=f'b_l_t_{teacher_id}_{week_date}'
                                                                    f'_{lesson_day.lesson_start}',
                                                        until_hour=lesson_day.student.teacher.until_minute_notification,
                                                        until_minute=lesson_day.student.teacher.until_hour_notification,
                                                        lesson_start=lesson_day.lesson_start,
                                                        week_date=week_date
                                                        )

        await session.commit()
    for x in await scheduler_storage.get_schedules():
        print(x.schedule_id)
    await scheduler_storage.shutdown()

@worker.task(task_name='notice_lesson_certain_time_teacher')
async def notice_lesson_certain_time_teacher(teacher_id: int,
                                             lesson_start: time,
                                             week_date: date,
                                             time_before_lesson: list,
                                             student_info,
                                             bot: Bot = TaskiqDepends(),
                                             context: Context = TaskiqDepends()):

    dt_res = datetime(year=week_date.year, month=week_date.month, day=week_date.day,
                      hour=lesson_start.hour, minute=lesson_start.minute)

    await bot.send_message(chat_id=teacher_id, text=LEXICON_TASKIQ['time_before_lesson_teacher']
                           .format(*student_info, *time_before_lesson, dt_res.strftime("%m.%d %H:%M")),
                           reply_markup=create_notice_lesson_certain_time_teacher_ok())

    async with context.state.session_pool() as session:
        await change_teacher_mailing_status(session,
                                            2,
                                            teacher_id,
                                            week_date,
                                            lesson_start)