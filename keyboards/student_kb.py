from datetime import date

from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


class FSMRegistrationStudentForm(StatesGroup):
    fill_name = State()
    fill_surname = State()
    fill_city = State()
    fill_place_study = State()
    fill_class_learning = State()
    fill_course_learning = State()
    fill_teacher = State()
    fill_price = State()


def create_entrance_kb():
    entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Авторизация',
                                  callback_data='auth_student')],
            [InlineKeyboardButton(text='Регистрация',
                                  callback_data='reg_student')]
        ],
    )
    return entrance_kb
