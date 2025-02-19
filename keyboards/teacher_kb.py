from datetime import date, time

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from callback_factory.teacher import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory, \
    DeleteDayCallbackFactory, ShowDaysOfScheduleTeacherCallbackFactory, ShowInfoDayCallbackFactory, \
     DeleteDayScheduleCallbackFactory
from database.teacher_requirements import give_student_by_student_id, give_student_by_student_id
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
            [InlineKeyboardButton(text='Мое расписание',
                                  callback_data='schedule_show')],
            [InlineKeyboardButton(text='Настройки',
                                  callback_data='settings_teacher')],
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


def create_add_remove_gap_kb():
    add_remove_gap_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Добавить',
                                  callback_data='add_gap_teacher')],
            [InlineKeyboardButton(text='Удалить',
                                  callback_data='remove_gap_teacher')],
            [InlineKeyboardButton(text='<назад',
                                  callback_data='schedule_teacher')]
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
                      callback_data=DeleteDayCallbackFactory
                          (
                          week_id=week_day.week_id
                      ).pack()
                  )
                  ]
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


async def show_status_lesson_day_kb(cur_buttons,
                                    session: AsyncSession,
                                    week_date_str: str):
    builder = InlineKeyboardBuilder()
    res_buttons = []

    for button in cur_buttons:
        # print(button)
        student = await give_student_by_student_id(session, button['student_id'])
        price = student.price / 2 * len(button['list_status'])
        status = '✅' if len(button['list_status']) == sum(button['list_status']) else '❌'
        res_buttons.append(
            InlineKeyboardButton(
                text=f'{status} {student.name} {button['lesson_on'].strftime("%H:%M")} - '
                     f'{button['lesson_off'].strftime("%H:%M")} {price} руб.',
                callback_data=EditStatusPayCallbackFactory(
                    lesson_on=button['lesson_on'].strftime("%H:%M"),
                    lesson_off=button['lesson_off'].strftime("%H:%M"),
                    week_date=week_date_str,
                ).pack()
            )
        )

    res_buttons.append(
        InlineKeyboardButton(text='<назад',
                             callback_data='confirmation_pay'
                             )
    )

    builder.row(*res_buttons, width=1)

    return builder.as_markup()


def show_next_seven_days_schedule_teacher_kb(*days):
    buttons = [
                  [InlineKeyboardButton(text=f'{cur_date.strftime("%d.%m")} - '
                                             f'{NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]}',
                                        callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                            week_date=cur_date.strftime("%Y-%m-%d")
                                        ).pack()
                                        )
                   ]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text='<назад',
                                         callback_data='auth_teacher')]]

    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return next_seven_days_with_cur_kb


def show_schedule_lesson_day_kb(cur_buttons,
                                session: AsyncSession,
                                week_date_str: str):
    builder = InlineKeyboardBuilder()
    res_buttons = []

    for button in cur_buttons:
        # print(button)
        # student = await give_student_by_student_id(session, button['student_id'])
        # price = student.price / 2 * len(button['list_status'])
        status_bool = len(button['list_status']) == sum(button['list_status'])
        status = '✅' if status_bool else '❌'
        res_buttons.append(
            InlineKeyboardButton(
                text=f'{status} {button['lesson_on'].strftime("%H:%M")} - '
                     f'{button['lesson_off'].strftime("%H:%M")}',
                callback_data=ShowInfoDayCallbackFactory(
                    lesson_on=button['lesson_on'].strftime("%H:%M"),
                    lesson_off=button['lesson_off'].strftime("%H:%M"),
                    week_date=week_date_str,
                    status=status_bool
                ).pack()
            )
        )

    # res_buttons.append(InlineKeyboardButton(text='Редактировать',
    #                                         callback_data=ShowDeleteLessonCallbackFactory(
    #                                             week_date=week_date_str
    #                                         ).pack()
    #                                         )
    #                    )

    res_buttons.append(
        InlineKeyboardButton(text='<назад',
                             callback_data='schedule_show'
                             )
    )

    builder.row(*res_buttons, width=1)

    return builder.as_markup()


def back_to_show_or_delete_schedule_teacher(week_date_str,
                                            lesson_on,
                                            lesson_off):
    return InlineKeyboardMarkup(inline_keyboard=
    [
        [InlineKeyboardButton(text='Удалить',
                              callback_data=DeleteDayScheduleCallbackFactory(
                                  week_date=week_date_str,
                                  lesson_on=lesson_on,
                                  lesson_off=lesson_off
                              ).pack()
                              )],
        [InlineKeyboardButton(text='<назад',
                              callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                  week_date=week_date_str
                              ).pack()
                              )
         ]
    ]
    )


def back_to_show_schedule_teacher(week_date_str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='<назад',
                              callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                  week_date=week_date_str
                              ).pack()
                              )
         ]
    ]
    )


def settings_teacher_kb():
    settings_teacher = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Заполнить профиль заново',
                                  callback_data='edit_profile')],
            [InlineKeyboardButton(text='❌Удалить профиль❌',
                                  callback_data='delete_profile')],
            [InlineKeyboardButton(text='<назад',
                                  callback_data='auth_teacher')]
        ]
    )

    return settings_teacher


