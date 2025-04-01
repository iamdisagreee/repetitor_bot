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
    give_information_for_day, give_student_by_student_id, give_lessons_for_day_students, give_lessons_for_day_teacher
from database.teacher_requests import give_all_lessons_day_by_week_day
from keyboards.taskiq_kb import create_confirmation_day_teacher_kb, create_confirmation_pay_student_kb, \
    create_notice_lesson_certain_time_student_ok
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from services.services import NUMERIC_DATE, give_date_format_fsm, show_intermediate_information_lesson_day_status, \
    give_time_format_fsm
from services.services_taskiq import give_data_config_teacher, give_everyday_schedule, create_schedule_like_text, \
    check_is_30_minutes_between, create_scheduled_task, change_to_specified_time, \
    give_correct_time_schedule_before_lesson, delete_unnecessary_tasks_teacher, give_dictionary_tasks_teacher


# Ежедневная рассылка для преподавателя и его учеников-должников
@worker.task(task_name='daily_newsletter_teacher')
async def daily_newsletter_teacher(teacher_id: int,
                                   context: Context = TaskiqDepends(),
                                   bot: Bot = TaskiqDepends()):
    async with context.state.session_pool() as session:
        teacher = await give_information_for_day(session, teacher_id)

    result_debtors, general_information = give_data_config_teacher(teacher)
    text = ''
    # print(result_debtors)
    for lesson in result_debtors:
        text += f" - {lesson['student_name']} {lesson['student_surname']} {int(lesson['amount_money'])}р." \
                f"{lesson['lesson_on'].strftime('%H:%M')}-{lesson['lesson_off'].strftime('%H:%M')}\n"
    await bot.send_message(chat_id=teacher_id,
                           text=LEXICON_TASKIQ['info_non_payment_teacher']
                           .format(datetime.now().strftime("%d.%m"),
                                   f"{general_information['amount_time'] // 3600} ч."
                                   f" {general_information['amount_time'] // 60 % 60} мин.",
                                   int(general_information['amount_money_yes']),
                                   int(general_information['amount_money_no']),
                                   text),
                           reply_markup=create_confirmation_day_teacher_kb()
                           )
    print('Сообщение отправлено преподавателю!')
    # Добавляем учеников в таблицу должников
    # uniq_debtors = set(debtor['teacher_id'] for debtor in result_debtors)
    async with context.state.session_pool() as session:
        for lesson in result_debtors:
            debtor = Debtor(
                teacher_id=teacher_id,
                student_id=lesson['student_id'],
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


# Высылаем расписание каждый день в __переданное время__
@worker.task(task_name='activities_day_teacher')
async def activities_day_teacher(teacher_id: int,
                                 context: Context = TaskiqDepends(),
                                 bot: Bot = TaskiqDepends()):
    async with context.state.session_pool() as session:
        teacher = await give_information_for_day(session,
                                                 teacher_id)

    result_schedule = give_everyday_schedule(teacher)
    text_schedule = create_schedule_like_text(result_schedule)

    await bot.send_message(chat_id=teacher_id, text=LEXICON_TASKIQ['give_everyday_schedule']
                           .format(text_schedule))

# Уведомление о занятии за какое-то время до начала
@worker.task(task_name='student_mailing_lessons')
async def student_mailing_lessons(context: Context = TaskiqDepends(),
                                  bot: Bot = TaskiqDepends()):
    await scheduler_storage.startup()

    scheduled_tasks = defaultdict(lambda: defaultdict(list))
    for task in await scheduler_storage.get_schedules():
        if task.schedule_id[0:5] == 'b_l_s':
            student_id, values = list(task.labels.items())[0]
            lesson_start, week_date = values
            scheduled_tasks[int(student_id)][give_date_format_fsm(week_date)] \
                            .append(give_time_format_fsm(lesson_start[:-3]))

    print(await scheduler_storage.get_schedules())

    async with (context.state.session_pool() as session):
        list_students_id = await give_lessons_for_day_students(session)
        # Смотрим расписание каждого студента по student_id
        # {student_id: {week_date: [12:30, 13:30, ...], week_date: [..],}, student_id2: ...}
        for student_id, dict_week_date in list_students_id.items():

            # {week_date: [12:30, 13:30, ...]}
            for week_date, lessons_day in dict_week_date.items():

                # Проверяем, что таска не удалена. Если удалена,
                # то меняем статус в обе стороны для всех занятий
                dict_lessons_day = dict((lesson_day.lesson_start, lesson_day)
                                       for lesson_day in lessons_day)

                # print('Словарь существующих уроков', dict_lessons_day)
                # print('Список запланированных задач', scheduled_tasks[student_id])

                for task_lesson_start in scheduled_tasks[student_id][week_date]:
                    # Если такого времени нет, то удаляем задачу и меняем статуса в левую и правую сторону
                    if task_lesson_start not in dict_lessons_day.keys():
                        await scheduler_storage.delete_schedule(f'b_l_s_{student_id}_{week_date}_{task_lesson_start}')
                        # print('Я УДАЛиЛИЛИЛИЛИЛИ')
                        left_time_lesson = task_lesson_start
                        right_time_lesson = task_lesson_start
                        while True:
                            hour, minute = change_to_specified_time(left_time_lesson, timedelta(minutes=-30))
                            left_time_lesson = time(hour=hour, minute=minute)
                            give_result_time = dict_lessons_day.get(left_time_lesson)
                            # print('GET_L', right_time_lesson, give_result_time)
                            if give_result_time is not None and give_result_time.student_mailing_status == 1:
                                give_result_time.student_mailing_status = 0
                            else:
                                break
                        while True:
                            # print('right_time_lesson', right_time_lesson)
                            hour, minute = change_to_specified_time(right_time_lesson, timedelta(minutes=30))
                            right_time_lesson = time(hour=hour, minute=minute)
                            give_result_time = dict_lessons_day.get(right_time_lesson)
                            # print('GET_R', right_time_lesson, give_result_time)
                            if give_result_time is not None and give_result_time.student_mailing_status == 1:
                                # print("AAA")
                                give_result_time.student_mailing_status = 0
                            else:
                                break

                print([x.student_mailing_status for x in lessons_day])
                if len(lessons_day) == 1:
                    if lessons_day[0].student_mailing_status == 0:
                        until_hour, until_minute = 0, 5
                        #Устанавливаем для отправления уведомлений
                        result_sent_time, until_hour, until_minute = \
                                            give_correct_time_schedule_before_lesson(lessons_day[0].lesson_start,
                                                                                     week_date,
                                                                                     until_hour,
                                                                                     until_minute)

                        # меняем статус и устанавливаем уведомление + добавляем в текущее хранилище
                        lessons_day[0].student_mailing_status = 1
                        await scheduler_storage.add_schedule(
                            create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                                  labels={str(student_id): [str(lessons_day[0].lesson_start),
                                                          str(lessons_day[0].week_date)]},
                                                  kwargs={'student_id': student_id,
                                                          'lesson_start': str(lessons_day[0].lesson_start),
                                                          'time_before_lesson': [until_hour, until_minute]
                                                          },
                                                  schedule_id=f'b_l_s_{student_id}_{week_date}_{lessons_day[0].lesson_start}',
                                                  time=result_sent_time + timedelta(seconds=5))
                                                  # cron='* * * * *',
                                                  # cron_offset='Europe/Moscow')
                        )
                        # scheduled_tasks[student_id].append(lessons_day[0].lesson_start)
                        print(f'Будет отправлено в {result_sent_time}')
                        continue

                for index, lesson_day in enumerate(lessons_day):
                    until_hour, until_minute = 0, 5
                    # print("INFO", lesson_day.student_mailing_status, index, lesson_day.lesson_start)
                    count_lessons = 0
                    static_index = index
                    if lesson_day.student_mailing_status == 0 and index + 1 < len(lessons_day):
                        for lesson_day_next in lessons_day[static_index + 1:]:
                            # print("INDEX", index)
                            if check_is_30_minutes_between(lesson_day.lesson_start,
                                                           lesson_day_next.lesson_start):
                                if lesson_day_next.student_mailing_status == 1:
                                    # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
                                    await scheduler_storage.delete_schedule(
                                        f'b_l_s_{student_id}_{week_date}_{lesson_day_next.lesson_start}')
                                    # print('Я DELETE')
                                    break
                                else:
                                    break
                            else:
                                break

                    if lesson_day.student_mailing_status == 1:
                        # Если статус равен единице и слева нет соседей, то ставим уведомление
                        if index != 0 and not check_is_30_minutes_between(lessons_day[index-1].lesson_start,
                                                                          lesson_day.lesson_start):
                            result_sent_time, until_hour, until_minute = \
                                give_correct_time_schedule_before_lesson(lesson_day.lesson_start,
                                                                         week_date,
                                                                         until_hour,
                                                                         until_minute)
                            await scheduler_storage.add_schedule(
                                create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                                      kwargs={'student_id': student_id,
                                                              'lesson_start': lesson_day.lesson_start,
                                                              'time_before_lesson': [until_hour, until_minute]
                                                              },
                                                      labels={str(student_id): [str(lesson_day.lesson_start),
                                                                                str(lesson_day.week_date)]},
                                                      schedule_id=f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}',
                                                      time=result_sent_time + timedelta(seconds=5)
                                                      # cron='* * * * *',
                                                      # cron_offset='Europe/Moscow'
                                                      )
                            )
                            print(f'Будет отправлено в {result_sent_time}')
                        continue

                    only_change = False

                    if index != 0 and lessons_day[index - 1].student_mailing_status == 1 and \
                            check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                        lessons_day[index].lesson_start):
                        only_change = True
                        # print("ПОПАЛ")

                    lesson_day.student_mailing_status = 1

                    if not only_change:

                        result_sent_time, until_hour, until_minute = \
                                            give_correct_time_schedule_before_lesson(lesson_day.lesson_start,
                                                                                     week_date,
                                                                                     until_hour,
                                                                                     until_minute)
                        await scheduler_storage.add_schedule(
                            create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                                  kwargs={'student_id': student_id,
                                                          'lesson_start': lesson_day.lesson_start,
                                                          'time_before_lesson': [until_hour, until_minute]
                                                          },
                                                  labels={str(student_id): [str(lesson_day.lesson_start),
                                                                            str(lesson_day.week_date)]},
                                                  schedule_id=f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}',
                                                  time=result_sent_time + timedelta(seconds=5)
                                                  # cron='* * * * *',
                                                  # cron_offset='Europe/Moscow'
                                                  )
                        )
                        print(f'Будет отправлено в {result_sent_time}')

        await session.commit()
    # print(scheduled_tasks)
    for x in await scheduler_storage.get_schedules():
        print(x.schedule_id)
    await scheduler_storage.shutdown()


# Уведомление о занятии за __переданное время__ до занятия для ученика
@worker.task(task_name='notice_lesson_certain_time_student')
async def notice_lesson_certain_time_student(student_id: int,
                                             lesson_start: time,
                                             time_before_lesson: list,
                                             context: Context = TaskiqDepends(),
                                             bot: Bot = TaskiqDepends()):

    await bot.send_message(chat_id=student_id, text=f'До занятия: {time_before_lesson[0]}'
                                                    f' ч. {time_before_lesson[1]} мин.\n'
                                                    f'Начало: {lesson_start.strftime("%H:%M")}',
                           reply_markup=create_notice_lesson_certain_time_student_ok())

    #После выполнения удаляем задачу
    # await scheduler_storage.startup()
    # await scheduler_storage.delete_schedule(f'b_l_{student_id}_{lesson_start.strftime("%H:%M")}')



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


                    if len(lessons_day) == 1 and lessons_day[0].student_mailing_status == 0:
                        #Тестовый вариант выборки времени
                        until_hour, until_minute = 5, 5
                        lessons_day[0].teacher_mailing_status = 1
                        await create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                                    labels={str(teacher_id): [lessons_day[0].student_id,
                                                                         lessons_day[0].lesson_start,
                                                                         lessons_day[0].week_date]},
                                                    kwargs={'teacher_id': teacher_id,
                                                            'lesson_start': lessons_day[0].lesson_start,
                                                            'time_before_lesson': [until_hour, until_minute],
                                                            'student_name': lessons_day[0].student.name
                                                            },
                                                    schedule_id=f'b_l_t_{teacher_id}_{week_date}'
                                                                f'_{lessons_day[0].lesson_start}',
                                                    until_hour=until_hour,
                                                    until_minute=until_minute,
                                                    lesson_start=lessons_day[0].lesson_start,
                                                    week_date=week_date
                                                    )
                        continue


                    for index, lesson_day in enumerate(lessons_day):
                        # Тестовый вариант выборки времени
                        until_hour, until_minute = 5, 5
                        static_index = index

                        if lesson_day.student_mailing_status == 0 and index + 1 < len(lessons_day):
                            for lesson_day_next in lessons_day[static_index + 1:]:
                                if check_is_30_minutes_between(lesson_day.lesson_start,
                                                               lesson_day_next.lesson_start):
                                    if lesson_day_next.student_mailing_status == 1:
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

                            await create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                                        labels={str(teacher_id): [lesson_day.student_id,
                                                                             lesson_day.lesson_start,
                                                                             lesson_day.week_date]},
                                                        kwargs={'teacher_id': teacher_id,
                                                                'lesson_start': lesson_day.lesson_start,
                                                                'time_before_lesson': [until_hour, until_minute],
                                                                'student_name': lesson_day.student.name
                                                                },
                                                        schedule_id=f'b_l_t_{teacher_id}_{week_date}'
                                                                    f'_{lesson_day.lesson_start}',
                                                        until_hour=until_hour,
                                                        until_minute=until_minute,
                                                        lesson_start=lesson_day.lesson_start,
                                                        week_date=week_date
                                                        )
                            continue


                        only_change = False
                        if index != 0 and lessons_day[index - 1].student_mailing_status == 1 and \
                                check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                            lessons_day[index].lesson_start):
                            only_change = True

                        lesson_day.teacher_mailing_status = 1

                        if not only_change:
                            await create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                                        labels={str(teacher_id): [lesson_day.student_id,
                                                                             lesson_day.lesson_start,
                                                                             lesson_day.week_date]},
                                                        kwargs={'teacher_id': teacher_id,
                                                                'lesson_start': lesson_day.lesson_start,
                                                                'time_before_lesson': [until_hour, until_minute],
                                                                'student_name': lesson_day.student.name
                                                                },
                                                        schedule_id=f'b_l_t_{teacher_id}_{week_date}'
                                                                    f'_{lesson_day.lesson_start}',
                                                        until_hour=until_hour,
                                                        until_minute=until_minute,
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
                                             time_before_lesson: list,
                                             student_name: str,
                                             bot: Bot = TaskiqDepends()):
    await bot.send_message(chat_id=teacher_id, text=f'{lesson_start} {student_name}')