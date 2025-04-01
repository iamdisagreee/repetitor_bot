from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from callback_factory.taskiq_factories import InformationLessonWithDeleteCallbackFactory
from lexicon.lexicon_taskiq import LEXICON_TASKIQ

def create_confirmation_day_teacher_kb():
    confirmation_day_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_TASKIQ['ok'],
                                     callback_data='confirmation_day_teacher')
            ]
        ]
    )
    return confirmation_day_teacher_kb

def create_confirmation_pay_student_kb(week_date: str,
                                       lesson_on: str,
                                       lesson_off: str,
                                       full_price: int
                                       ):
    confirmation_pay_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=LEXICON_TASKIQ['confirm_payment_student'],
                                     callback_data=InformationLessonWithDeleteCallbackFactory(
                                         week_date=week_date,
                                         lesson_on=lesson_on,
                                         lesson_off=lesson_off,
                                         full_price=full_price
                                     ).pack()),
            ]
        ]
    )
    return confirmation_pay_student_kb

def create_notice_lesson_certain_time_student_ok():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TASKIQ['ok'],
                                  callback_data='notice_lesson_certain_time_student')]
        ]
    )

def create_notice_lesson_certain_time_teacher_ok():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TASKIQ['ok'],
                                  callback_data='notice_lesson_certain_time_teacher')]
        ]
    )
