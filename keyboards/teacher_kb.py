from datetime import date

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from callback_factory.teacher import ShowDaysOfPayCallbackFactory
from services.services import NUMERIC_DATE


def create_entrance_kb():
    entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text='Авторизация',
                                                  callback_data='auth_teacher')],
                            [InlineKeyboardButton(text='Регистрация',
                                                  callback_data='reg_teacher')]
                        ] + [
                            [InlineKeyboardButton(text='<назад',
                                                  callback_data='start')]
                        ]
    )
    return entrance_kb


def create_back_to_entrance_kb():
    back_to_entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text='Перейти в меню идентификации!',
                callback_data='teacher_entrance')
            ]
        ]
    )

    return back_to_entrance_kb


def create_authorization_kb():
    authorization_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Настройка расписания',
                                  callback_data='schedule_teacher')],
            [InlineKeyboardButton(text='Подтверждение оплаты',
                                  callback_data='confirmation_pay')],
            [InlineKeyboardButton(text='<назад',
                                  callback_data='teacher_entrance')
             ]
        ]
    )
    return authorization_kb


def show_next_seven_days_kb(*days, back):
    buttons = [
                  [InlineKeyboardButton(text=f'{cur_date.strftime("%d.%m")} - '
                                             f'{NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]}',
                                        callback_data=cur_date.strftime("%Y-%m-%d"))
                   ]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text=back,
                                         callback_data='auth_teacher')]]
    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return next_seven_days_with_cur_kb


def create_add_remove_gap_kb(back: str):
    add_remove_gap_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Добавить',
                                  callback_data='add_gap_teacher')],
            [InlineKeyboardButton(text='Удалить',
                                  callback_data='remove_gap_teacher')],
            [InlineKeyboardButton(text=back,
                                  callback_data='auth_teacher')]
        ]
    )

    return add_remove_gap_kb


def create_back_to_profile_kb(time_to_repeat: str):
    buttons = [[InlineKeyboardButton(text='Вернемся в меню выбора действия!',
                                     callback_data=time_to_repeat)],
               ]

    back_to_profile_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return back_to_profile_kb


def create_all_records_week_day(weeks_day):
    buttons = [
                  [InlineKeyboardButton(
                      text=f'{week_day.work_start.strftime("%H:%M")} - '
                           f'{week_day.work_end.strftime("%H:%M")}',
                      callback_data=f'del_record_teacher_{week_day.week_id}')]
                  for week_day in weeks_day
              ] + [
                  [InlineKeyboardButton(
                      text='<назад',
                      callback_data='schedule_teacher'
                  )]
              ]
    all_records_week_day_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return all_records_week_day_kb


def show_next_seven_days_pay_kb(*days):
    buttons = [
                  [InlineKeyboardButton(text=f'{cur_date.strftime("%d.%m")} - '
                                             f'{NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]}',
                                        callback_data=ShowDaysOfPayCallbackFactory(
                                            week_date=cur_date.strftime("%Y-%m-%d")
                                        ).pack()
                                        )
                   ]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text='<назад',
                                         callback_data='auth_teacher')]]

    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return next_seven_days_with_cur_kb
