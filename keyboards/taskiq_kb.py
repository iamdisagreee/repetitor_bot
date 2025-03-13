from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from callback_factory.student_factories import InformationLessonCallbackFactory
from callback_factory.teacher_factories import SentMessagePaymentStudentCallbackFactory
from lexicon.lexicon_taskiq import LEXICON_TASKIQ
from lexicon.lexicon_teacher import LEXICON_TEACHER


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