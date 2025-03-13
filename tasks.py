import asyncio
from datetime import datetime, date, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from broker import worker
from callback_factory.student_factories import InformationLessonCallbackFactory
from database import AccessStudent, Teacher, Debtor
from taskiq import Context, TaskiqDepends

from sqlalchemy import select

from database.taskiq_requests import give_scheduled_payment_verification_students, \
     give_information_for_day
from database.teacher_requests import give_all_lessons_day_by_week_day
from keyboards.taskiq_kb import create_confirmation_day_teacher_kb
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from services.services import NUMERIC_DATE, give_date_format_fsm, show_intermediate_information_lesson_day_status
from services.services_taskiq import give_data_config_teacher


#Таска, которая отправляет всем неоплаченным студентам уведомление о неоплате!
@worker.task(task_name='scheduled_payment_verification')
async def scheduled_payment_verification(context: Context = TaskiqDepends(),
                                         bot: Bot = TaskiqDepends()
                                         ):

    async with context.state.session_pool() as session:
            list_not_paid_student = iter(await give_scheduled_payment_verification_students(session))
            # list_not_paid_teachers = iter()
    # Работа с сообщениями для учеников
    while True:
        try:
            for student_id in list_not_paid_student:
                # print(student)
                try:
                    await bot.send_message(student_id, LEXICON_TASKIQ['forget_paid_students']
                                           .format(datetime.now().strftime("%d.%m")))
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

#Ежедневная рассылка для преподавателя
@worker.task(task_name='daily_newsletter_teacher')
async def daily_newsletter_teacher(teacher_id: int,
                                   context: Context = TaskiqDepends(),
                                   bot: Bot = TaskiqDepends()):
    async with context.state.session_pool() as session:
        teacher = await give_information_for_day(session, teacher_id)

    result_debtors, general_information = give_data_config_teacher(teacher)
    text = ''
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

    #Добавляем учеников в таблицу должников
    # uniq_debtors = set(debtor['teacher_id'] for debtor in result_debtors)
    async with context.state.session_pool() as session:
        for lesson in result_debtors:
            debtor = Debtor(
                teacher_id=teacher_id,
                student_id=lesson['student_id'],
                lesson_on=lesson['lesson_on'],
                lesson_off=lesson['lesson_off']
            )
            await session.add(debtor)


    #Начинаем рассылку для учеников (???)
    iter_result_debtors = iter(result_debtors)
    while True:
        try:
            for student in iter_result_debtors:
                # print(student)
                try:
                    await bot.send_message(student['student_id'], LEXICON_TASKIQ['forget_paid_students']
                                           .format(datetime.now().strftime("%d.%m")))
                except TelegramForbiddenError:
                    pass
            break
        # except TimeoutError:
        #     print("Рассылка закончена")
        #     break
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after))
            continue
    #Работа с сообщениями для преподавателей
    # async with context.state.session_pool() as session:
    #     list_not_paid_teachers = iter(await give_scheduled_payment_verification_teachers(session))
    #     information_day = await give_information_for_day(session)
    # data_config_res = give_data_config_teacher(information_day)
    # while True:
    #     try:
    #         for teacher in list_not_paid_teachers:
    #             #При условии, что есть должники
    #             data_config_cur = data_config_res.get(teacher.teacher_id)
    #             create_list_students = '/n'.join(f'  - {student.name} {student.surname}'
    #                                                      for student in teacher.students)
    #             time_cur = data_config_cur['amount_time']
    #             await bot.send_message(teacher.teacher_id, LEXICON_TASKIQ['info_non_payment_teacher']
    #                                         .format(datetime.now().strftime("%d.%m"),
    #                                                 f'{time_cur // 3600} ч.'
    #                                                 f' {time_cur // 60 % 60} мин.',
    #                                                 data_config_cur['amount_money_yes'],
    #                                                 data_config_cur['amount_money_no'],
    #                                                 create_list_students))
    #
    #         break
    #     except TelegramRetryAfter as e:
    #             await asyncio.sleep(float(e.retry_after))
    #             continue
    # print('Рассылка для преподавателей окончена!!')

# @worker.task
# async def sent_student_payment_confirmation(teacher_id: int,
#                                             student_id: int,
#                                             callback_data: InformationLessonCallbackFactory,
#                                             bot: Bot = TaskiqDepends()):
#     week_date = give_date_format_fsm(callback_data.week_date)
#     await bot.send_message(chat_id=teacher_id,
#                            text=LEXICON_TASKIQ['sent_student_payment_confirmation']
#                            .format(callback_data.name, callback_data.surname,
#                                    callback_data.subject, week_date.strftime("%d.%m"),
#                                    NUMERIC_DATE[date(year=week_date.year,
#                                                      month=week_date.month,
#                                                      day=week_date.day).isoweekday()],
#                                    callback_data.lesson_on, callback_data.lesson_off,
#                                    callback_data.full_price),
#                            reply_markup=create_confirm_payment_teacher_kb(student_id,
#                                                                           callback_data)
#                            )