from datetime import date

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def create_start_kb():
    buttons = [
        [InlineKeyboardButton(text='Ученик',
                              callback_data='student_entrance')],
        [InlineKeyboardButton(text='Преподаватель',
                              callback_data='teacher_entrance')]
    ]
    start_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return start_kb
