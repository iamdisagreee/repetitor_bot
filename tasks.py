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
    give_information_for_day, give_student_by_student_id, give_lessons_for_day_students
from database.teacher_requests import give_all_lessons_day_by_week_day
from keyboards.taskiq_kb import create_confirmation_day_teacher_kb, create_confirmation_pay_student_kb
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from services.services import NUMERIC_DATE, give_date_format_fsm, show_intermediate_information_lesson_day_status, \
    give_time_format_fsm
from services.services_taskiq import give_data_config_teacher, give_everyday_schedule, create_schedule_like_text, \
    check_is_30_minutes_between, create_scheduled_task


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

@worker.task(task_name='student_mailing_lessons_student')
async def student_mailing_lessons_student(context: Context = TaskiqDepends(),
                                  bot: Bot = TaskiqDepends()):

    await scheduler_storage.startup()

    scheduled_tasks = defaultdict(list)
    for task in await scheduler_storage.get_schedules():
        (scheduled_tasks[int(list(task.labels.keys())[0])]
         .append(give_time_format_fsm(list(task.labels.values())[0][:-3])))

    print(scheduled_tasks)
    print(await scheduler_storage.get_schedules())

    async with context.state.session_pool() as session:
        list_students_id = await give_lessons_for_day_students(session)

        #Смотрим расписание каждого студента по student_id
        for student_id, lessons_day in list_students_id.items():

            if len(lessons_day) == 1:
                if lessons_day[0].student_mailing_status == 0:
                    # меняем статус и устанавливаем уведомление + добавляем в текущее хранилище
                    lessons_day[0].student_mailing_status = 1
                    await scheduler_storage.add_schedule(
                        create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                              labels={str(student_id): lessons_day[0].lesson_start},
                                              args=[student_id],
                                              schedule_id=f'b_l_{student_id}_{str(lessons_day[0].lesson_start)}',
                                              time=datetime.now() + timedelta(seconds=10))
                    )
                    scheduled_tasks[student_id].append(lessons_day[0].lesson_start)
                    continue

            need_change = 0
            for index, lesson_day in enumerate(lessons_day):
                count_lessons = 0
                # print("INFO", lesson_day.student_mailing_status, index, len(lessons_day))
                if lesson_day.student_mailing_status == 0 and index+1 < len(lessons_day):
                    for lesson_day_next in lessons_day[index+1:]:
                        # print("INDEX", index)
                        if check_is_30_minutes_between(lesson_day.lesson_start,
                                                       lesson_day_next.lesson_start):
                            if lesson_day_next.student_mailing_status == 1:
                                need_change = 1
                                # удаляем текущее уведомление (lesson_day_next.student_mailing_status)
                                await scheduler_storage.delete_schedule(f'b_l_{student_id}_{lesson_day_next.lesson_start}')
                                break
                            else:
                                count_lessons += 1
                        else:
                            # print('aaaaaaaaaaaaaaaaaa')
                            break

                        index += 1

                # #Случай, когда в конце один интервал со статусом 0
                # if count_lessons == 0 and lessons_day[index].student_mailing_status == 0:
                #     count_lessons += 1

                only_change = False
                if count_lessons == 0 or count_lessons != 0:
                    #Условие когда добавили в конец
                    if index != 0 and lessons_day[index-1].student_mailing_status == 1 and \
                        check_is_30_minutes_between(lessons_day[index-1].lesson_start, lessons_day[index].lesson_start):
                            only_change = True
                            #Меняем все значение в диапазоне [index-count_lessons:index++1]
                    else:
                        #Случай, когда добавили в середине, но уведомления уже проставлены раньше
                        decreasing_index = index
                        while decreasing_index > 0:
                            if check_is_30_minutes_between(lessons_day[decreasing_index-1].lesson_start,
                                                            lessons_day[decreasing_index].lesson_start) \
                                        and lessons_day[decreasing_index-1].student_mailing_status == 1:
                                only_change = True
                                break

                            decreasing_index -= 1

                        #Меняем все в диапазоне [index-count_lessons:index+1]
                        for change_lesson_day in lessons_day[index-count_lessons: index+1]:
                            # print(index, f'Поменял для {change_lesson_day.lesson_start}')
                            change_lesson_day.student_mailing_status = 1

                        if not only_change:
                            await scheduler_storage.add_schedule(
                                create_scheduled_task(task_name='notice_lesson_certain_time_student',
                                                      kwargs={'student_id': student_id},
                                                      labels={str(student_id): str(lesson_day.lesson_start)},
                                                      schedule_id=f'b_l_{student_id}_{lesson_day.lesson_start}',
                                                      time=datetime.now(timezone.utc) + timedelta(seconds=10)
                                                      )
                            )
                            scheduled_tasks[student_id].append(lesson_day.lesson_start)
                            #И ставим уведомление на index - count_lessons
                    # Меняем все в диапазоне [index-count_lessons:index+1]
                    # И ставим уведомление на index - count_lessons
                    # if need_change and count_lessons == 0:
                    #     for change_lesson_day in lessons_day[index - count_lessons: index + 1]:
                    #         change_lesson_day.student_mailing_status = 1
                    #     await scheduler_storage.add_schedule(
                    #         create_scheduled_task(task_name='notice_lesson_certain_time_student',
                    #                               kwargs={'student_id':student_id},
                    #                               labels={str(student_id): lesson_day.lesson_start},
                    #                               schedule_id=f'b_l_{student_id}_{lesson_day.lesson_start}',
                    #                               time=datetime.now() + timedelta(seconds=5)
                    #                               )
                    #     )
                    #     scheduled_tasks[student_id].append(lesson_day.lesson_start)

        await session.commit()
        print(scheduled_tasks)
        print(await scheduler_storage.get_schedules())


# Уведомление о занятии за __переданное время__ до занятия для ученика
@worker.task(task_name='notice_lesson_certain_time_student')
async def notice_lesson_certain_time_student(student_id: int,
                                           context: Context = TaskiqDepends(),
                                           bot: Bot = TaskiqDepends()):
    # async with context.state.session_pool() as session:
    #     student = await give_student_by_student_id(session, student_id)

    await bot.send_message(chat_id=859717714, text='auf')