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
    give_correct_time_schedule_before_lesson


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
    # print()
    # print(scheduled_tasks)
    # print(await scheduler_storage.get_schedules())

    async with (context.state.session_pool() as session):
        list_students_id = await give_lessons_for_day_students(session)
        until_hour, until_minute = 0, 30
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
                        )
                        # scheduled_tasks[student_id].append(lessons_day[0].lesson_start)
                        print(f'Будет отправлено в {result_sent_time}')
                        continue

                for index, lesson_day in enumerate(lessons_day):
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
                                        f'b_l_s_{student_id}_{week_date}_{lesson_day.lesson_start}')
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
                                                      )
                            )
                            print(f'Будет отправлено в {result_sent_time}')
                        continue

                    # #Случай, когда в конце один интервал со статусом 0
                    # if count_lessons == 0 and lessons_day[index].student_mailing_status == 0:
                    #     count_lessons += 1

                    only_change = False
                    # Условие когда добавили в конец
                    #Информация:
                    # print('GOO', static_index, index, lessons_day[index - 1].student_mailing_status == 1, check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                    #                                                                                   ?           lessons_day[index].lesson_start),
                          # lessons_day[index-1].lesson_start, lessons_day[index].lesson_start)
                    if index != 0 and lessons_day[index - 1].student_mailing_status == 1 and \
                            check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                        lessons_day[index].lesson_start):
                        only_change = True
                        # print("ПОПАЛ")


                    # print('FULL INFO', index, count_lessons, only_change)
                    # Меня м все в диапазоне [index-count_lessons:index+1]
                    # for change_lesson_day in lessons_day[index - count_lessons: index + 1]:
                        # print(index, f'Поменял для {change_lesson_day.lesson_start}')
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
                                                    f' ч. {time_before_lesson[1]} мин.',
                           reply_markup=create_notice_lesson_certain_time_student_ok())

    #После выполнения удаляем задачу
    # await scheduler_storage.startup()
    # await scheduler_storage.delete_schedule(f'b_l_{student_id}_{lesson_start.strftime("%H:%M")}')



# Уведомление о занятии за какое-то время до начала для репетитора
@worker.task(task_name='teacher_mailing_lessons')
async def teacher_mailing_lessons(context: Context = TaskiqDepends(),
                                          bot: Bot = TaskiqDepends()):
    await scheduler_storage.startup()


    scheduled_tasks = defaultdict(list)
    for task in await scheduler_storage.get_schedules():
        if task.schedule_id[0:5] == 'b_l_t':
            scheduled_tasks[int(list(task.labels.keys())[0])] \
                .append(give_time_format_fsm(list(task.labels.values())[0][:-3]))

    print(scheduled_tasks)
    print(await scheduler_storage.get_schedules())

    async with context.state.session_pool() as session:
        list_teachers_id = await give_lessons_for_day_teacher(session)

        # Смотрим расписание каждого студента по student_id
        for teacher_id, lessons_day in list_teachers_id.items():

            #Указываем время для уведомлений
            # time_sent = give_correct_time_schedule_before_lesson

            # Проверяем, что таска не удалена. Если удалена,
            # то меняем статус в обе стороны для всех занятий
            dict_lessons_day = dict((lesson_day.lesson_start, lesson_day)
                                    for lesson_day in lessons_day)

            # print('Словарь существующих уроков', dict_lessons_day)
            # print('Список запланированных задач', scheduled_tasks[student_id])

            for task_lesson_start in scheduled_tasks[teacher_id]:
                # Если такого времени нет, то удаляем задачу и меняем статуса в левую и правую сторону
                if task_lesson_start not in dict_lessons_day.keys():
                    await scheduler_storage.delete_schedule(f'b_l_t_{teacher_id}_{task_lesson_start}')

                    left_time_lesson = task_lesson_start
                    right_time_lesson = task_lesson_start
                    while True:
                        hour, minute = change_to_specified_time(left_time_lesson, timedelta(minutes=-30))
                        left_time_lesson = time(hour=hour, minute=minute)
                        give_result_time = dict_lessons_day.get(left_time_lesson)
                        # print('GET_L', right_time_lesson, give_result_time)
                        if give_result_time is not None and give_result_time.teacher_mailing_status == 1:
                            give_result_time.teacher_mailing_status = 0
                        else:
                            break
                    while True:
                        # print('right_time_lesson', right_time_lesson)
                        hour, minute = change_to_specified_time(right_time_lesson, timedelta(minutes=30))
                        right_time_lesson = time(hour=hour, minute=minute)
                        give_result_time = dict_lessons_day.get(right_time_lesson)
                        # print('GET_R', right_time_lesson, give_result_time)
                        if give_result_time is not None and give_result_time.teacher_mailing_status == 1:
                            # print("AAA")
                            give_result_time.teacher_mailing_status = 0
                        else:
                            break

            # print([x.student_mailing_status for x in lessons_day])
            if len(lessons_day) == 1:
                if lessons_day[0].teacher_mailing_status == 0:
                    # меняем статус и устанавливаем уведомление + добавляем в текущее хранилище
                    lessons_day[0].teacher_mailing_status = 1
                    await scheduler_storage.add_schedule(
                        create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                              labels={str(teacher_id): str(lessons_day[0].lesson_start)},
                                              kwargs={'teacher_id': teacher_id,
                                                      'lesson_start': str(lessons_day[0].lesson_start)},
                                              schedule_id=f'b_l_t_{teacher_id}_{lessons_day[0].lesson_start}',
                                              time=datetime.now(timezone.utc) + timedelta(seconds=10))
                    )
                    # scheduled_tasks[student_id].append(lessons_day[0].lesson_start)
                    continue

            need_change = 0
            for index, lesson_day in enumerate(lessons_day):
                count_lessons = 0
                # print("INFO", lesson_day.student_mailing_status, index, len(lessons_day))
                static_index = index
                if lesson_day.teacher_mailing_status == 0 and index + 1 < len(lessons_day):
                    for lesson_day_next in lessons_day[static_index + 1:]:
                        # print("INDEX", index)
                        if check_is_30_minutes_between(lesson_day.lesson_start,
                                                       lesson_day_next.lesson_start):
                            if lesson_day_next.teacher_mailing_status == 1:
                                # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
                                # print('aue')
                                await scheduler_storage.delete_schedule(
                                    f'b_l_t_{teacher_id}_{lesson_day_next.lesson_start}')
                                break
                            else:
                                count_lessons += 1
                        else:
                            break

                        index += 1

                if lesson_day.teacher_mailing_status == 1:
                    # Если статус равен единице и слева нет соседей, то ставим уведомление
                    if index != 0 and not check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                                      lesson_day.lesson_start):
                        await scheduler_storage.add_schedule(
                            create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                                  kwargs={'teacher_id': teacher_id,
                                                          'lesson_start': lesson_day.lesson_start},
                                                  labels={str(teacher_id): str(lesson_day.lesson_start)},
                                                  schedule_id=f'b_l_t_{teacher_id}_{lesson_day.lesson_start}',
                                                  cron='* * * * *',
                                                  cron_offset='Europe/Moscow',
                                                  # time=datetime.now(timezone.utc) + timedelta(seconds=10)
                                                  )
                        )
                    continue
                # #Случай, когда в конце один интервал со статусом 0
                # if count_lessons == 0 and lessons_day[index].student_mailing_status == 0:
                #     count_lessons += 1

                only_change = False
                # Условие когда добавили в конец
                if index != 0 and lessons_day[index - 1].teacher_mailing_status == 1 and \
                        check_is_30_minutes_between(lessons_day[index - 1].lesson_start,
                                                    lessons_day[index].lesson_start):
                    only_change = True
                    # print("ПОПАЛ")

                # print('FULL INFO', index, count_lessons, only_change)
                # Меня м все в диапазоне [index-count_lessons:index+1]
                for change_lesson_day in lessons_day[index - count_lessons: index + 1]:
                    # print(index, f'Поменял для {change_lesson_day.lesson_start}')
                    change_lesson_day.teacher_mailing_status = 1

                if not only_change:
                    await scheduler_storage.add_schedule(
                        create_scheduled_task(task_name='notice_lesson_certain_time_teacher',
                                              kwargs={'teacher_id': teacher_id,
                                                      'lesson_start': lesson_day.lesson_start},
                                              labels={str(teacher_id): str(lesson_day.lesson_start)},
                                              schedule_id=f'b_l_t_{teacher_id}_{lesson_day.lesson_start}',
                                              cron='* * * * *',
                                              cron_offset='Europe/Moscow',
                                              # time=datetime.now(timezone.utc) + timedelta(seconds=10)
                                              )
                    )
        await session.commit()
    # print(scheduled_tasks)
    for x in await scheduler_storage.get_schedules():
        print(x.schedule_id)
    await scheduler_storage.shutdown()

@worker.task(task_name='notice_lesson_certain_time_teacher')
async def notice_lesson_certain_time_teacher(teacher_id: int,
                                             lesson_start: time,
                                             bot: Bot = TaskiqDepends()):
    await bot.send_message(chat_id=teacher_id, text=str(lesson_start))