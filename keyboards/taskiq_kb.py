from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from callback_factory.student_factories import InformationLessonCallbackFactory
from callback_factory.teacher_factories import SentMessagePaymentStudentCallbackFactory
from lexicon.lexicon_taskiq import LEXICON_TASKIQ


def create_confirm_payment_teacher_kb(student_id: int,
                                      callback_data: InformationLessonCallbackFactory):
    confirm_payment_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=LEXICON_TASKIQ['confirm_payment_student'],
                callback_data=SentMessagePaymentStudentCallbackFactory(
                    student_id=student_id,
                    week_date=callback_data.week_date,
                    lesson_on=callback_data.lesson_on,
                    lesson_off=callback_data.lesson_off
                ).pack()
            )]
        ]
    )

    return confirm_payment_teacher_kb