from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def create_entrance_kb():
    entrance_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Авторизация')],
                                                [KeyboardButton(text='Регистрация')]],
                                      resize_keyboard=True)
    return entrance_kb


def create_back_to_entrance_kb():
    back_to_entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text='Перейти в меню идентификации!',
            callback_data='teacher_entrance')]]
    )

    return back_to_entrance_kb


def create_authorization_kb():
    authorization_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Расписание')],
                                                     [KeyboardButton(text='Подтверждение')]],
                                           resize_keyboard=True,
                                           one_time_keyboard=True)
    return authorization_kb


def show_next_seven_days_kb(**days):
    buttons = [
        [KeyboardButton(text=f'{cur_date} - {cur_name}')]
        for cur_date, cur_name in days.items()
    ]
    print(buttons)
    next_seven_days_kb = ReplyKeyboardMarkup(keyboard=buttons,
                                             resize_keyboard=True)

    return next_seven_days_kb
