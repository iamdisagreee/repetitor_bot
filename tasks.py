import asyncio
from datetime import datetime, date

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from broker import worker
from callback_factory.student_factories import InformationLessonCallbackFactory
from database import AccessStudent
from taskiq import Context, TaskiqDepends

from sqlalchemy import select

from database.taskiq_requests import give_scheduled_payment_verification_students, \
    give_scheduled_payment_verification_teachers
from keyboards.taskiq_kb import create_confirm_payment_teacher_kb
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from services.services import NUMERIC_DATE, give_date_format_fsm


#Таска, которая отправляет всем неоплаченным студентам уведомление о неоплате!
#Также сообщает преподавателю, что такой-то такой-то не оплатил занятие
@worker.task(task_name='scheduled_payment_verification')
async def scheduled_payment_verification(context: Context = TaskiqDepends(),
                                         bot: Bot = TaskiqDepends()
                                         ):

    async with context.state.session_pool() as session:
            list_not_paid_student = iter(await give_scheduled_payment_verification_students(session))
            # list_not_paid_teachers = iter()
    # Работа с сообщениями для учеников
    #list_not_paid_students = [lesson.student_id for student in list_not_paid_info]
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

    #Работа с сообщениями для преподавателей
    async with context.state.session_pool() as session:
        list_not_paid_teachers = iter(await give_scheduled_payment_verification_teachers(session))

    while True:
        try:
            for teacher in list_not_paid_teachers:
                #При условии, что есть должникиs
                if teacher.students:
                    create_list_students = '/n'.join(f'{student.name} {student.surname}'
                                                     for student in teacher.students)
                    await bot.send_message(teacher.teacher_id, LEXICON_TASKIQ['info_non_payment_teacher']
                                           .format(datetime.now().strftime("%d.%m"), create_list_students))
                else:
                    await bot.send_message(teacher.teacher_id, LEXICON_TASKIQ['info_good_day']
                                           .format(datetime.now().strftime("%d.%m")))
            break
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after))
            continue
    print('Рассылка для преподавателей окончена!!')


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