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
from keyboards.taskiq_kb import create_confirmation_day_teacher_kb, create_confirmation_pay_student_kb
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from services.services import NUMERIC_DATE, give_date_format_fsm, show_intermediate_information_lesson_day_status
from services.services_taskiq import give_data_config_teacher

# Ежедневная рассылка для преподавателя и его учеников-должников
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

# @worker.task(task_name='')