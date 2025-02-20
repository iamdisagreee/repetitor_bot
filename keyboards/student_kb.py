from datetime import date, timedelta, datetime, time

from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callback_factory.student import ExistFieldCallbackFactory, EmptyAddFieldCallbackFactory, \
    DeleteFieldCallbackFactory, EmptyRemoveFieldCallbackFactory, ShowDaysOfScheduleCallbackFactory, \
    StartEndLessonDayCallbackFactory, PlugPenaltyStudentCallbackFactory
from services.services import NUMERIC_DATE


def create_entrance_kb():
    entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text='Авторизация',
                                                  callback_data='auth_student')],
                            [InlineKeyboardButton(text='Регистрация',
                                                  callback_data='reg_student')]
                        ] + [
                            [InlineKeyboardButton(text='<назад',
                                                  callback_data='start')]
                        ]
    )
    return entrance_kb


def create_level_choice_kb():
    level_choice_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Класс обучения'),
             KeyboardButton(text='Курс обучения')]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    return level_choice_kb


def create_teachers_choice_kb(teachers):
    teacher_choice_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'{teacher.surname} {teacher.name}',
                                  callback_data=str(teacher.teacher_id))]
            for teacher in teachers
        ]
    )
    return teacher_choice_kb


def create_back_to_entrance_kb():
    back_to_entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text='Перейти в меню идентификации!',
            callback_data='student_entrance')]]
    )

    return back_to_entrance_kb


def create_authorization_kb():
    authorization_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Настройки расписания',
                                  callback_data='settings_schedule')],
            [InlineKeyboardButton(text='Мое расписание',
                                  callback_data='show_schedule')],
            [InlineKeyboardButton(text='Настройки',
                                  callback_data='settings_student')],
            [InlineKeyboardButton(text='Штрафы',
                                  callback_data='penalties')],
            [InlineKeyboardButton(text='<назад',
                                  callback_data='student_entrance')]
        ],
    )

    return authorization_kb


def show_next_seven_days_settings_kb(*days):
    buttons = [
                  [InlineKeyboardButton(text=f'{cur_date.strftime("%d.%m")} - '
                                             f'{NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]}',
                                        callback_data=cur_date.strftime("%Y-%m-%d"))]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text='<назад',
                                         callback_data='auth_student')]]

    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return next_seven_days_with_cur_kb


def create_menu_add_remove_kb():
    add_remove_gap_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Добавить',
                                  callback_data='add_gap_student')],
            [InlineKeyboardButton(text='Удалить',
                                  callback_data='remove_gap_student')],
            [InlineKeyboardButton(text='<назад',
                                  callback_data='settings_schedule')]
        ]
    )

    return add_remove_gap_kb


def create_choose_time_student_kb(dict_lessons,
                                  week_date_str,
                                  page):
    builder = InlineKeyboardBuilder()

    counter_buttons = 0
    for lesson in dict_lessons[page]:
        if lesson:
            builder.button(
                text=f'{lesson['lesson_start'].strftime("%H:%M")}-{lesson['lesson_end'].strftime("%H:%M")}',
                callback_data=ExistFieldCallbackFactory(
                    lesson_start=lesson['lesson_start'].strftime("%H:%M"),
                    lesson_finished=lesson['lesson_end'].strftime("%H:%M")
                )
            )
            counter_buttons += 1

    while counter_buttons < 6:
        builder.button(
            text='     ',
            callback_data=EmptyAddFieldCallbackFactory(
                plug=''
            )
        )
        counter_buttons += 1

    builder.button(text='<<',
                   callback_data='move_left_add')
    builder.button(text='>>',
                   callback_data='move_right_add')
    builder.button(text='выйти',
                   callback_data=week_date_str)

    builder.adjust(2, 2, 2, 2, 1)

    return builder.as_markup()


def create_delete_lessons_menu(dict_for_6_lessons,
                               week_date_str,
                               page):
    builder = InlineKeyboardBuilder()
    counter_buttons = 0
    for lesson in dict_for_6_lessons[page]:
        builder.button(
            text=f'{lesson.lesson_start.strftime("%H:%M")} - {lesson.lesson_finished.strftime("%H:%M")}',
            callback_data=DeleteFieldCallbackFactory(
                lesson_start=lesson.lesson_start.strftime("%H:%M"),
                lesson_finished=lesson.lesson_finished.strftime("%H:%M")
            )
        )
        counter_buttons += 1
    while counter_buttons < 6:
        builder.button(
            text='     ',
            callback_data=EmptyRemoveFieldCallbackFactory(
                plug=''
            )
        )
        counter_buttons += 1

    builder.button(text='<<',
                   callback_data='move_left_remove')
    builder.button(text='>>',
                   callback_data='move_right_remove')
    builder.button(text='выйти',
                   callback_data=week_date_str)

    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def show_next_seven_days_schedule_kb(*days):
    buttons = [
                  [InlineKeyboardButton(text=f'{cur_date.strftime("%d.%m")} - '
                                             f'{NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]}',
                                        callback_data=ShowDaysOfScheduleCallbackFactory(
                                            week_date=cur_date.strftime("%Y-%m-%d")
                                        ).pack()
                                        )
                   ]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text='<назад',
                                         callback_data='auth_student')]]

    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return next_seven_days_with_cur_kb


def all_lessons_for_day_kb(lessons):
    builder = InlineKeyboardBuilder()
    buttons = []
    for lesson in lessons:
        buttons.append(
            InlineKeyboardButton(
                text=f'{lesson['start'].strftime("%H:%M")} - {lesson['finished'].strftime("%H:%M")}',
                callback_data=StartEndLessonDayCallbackFactory
                    (
                    lesson_on=lesson['start'].strftime("%H:%M"),
                    lesson_off=lesson['finished'].strftime("%H:%M")
                ).pack()
            )
        )
    buttons.append(InlineKeyboardButton(text='<назад',
                                        callback_data='show_schedule')
                   )

    builder.row(*buttons, width=1)
    return builder.as_markup()


def create_button_for_back_to_all_lessons_day(week_date):
    button_for_back_to_all_lessons_day = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='<назад',
                                  callback_data=ShowDaysOfScheduleCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  )
             ]
        ]
    )

    return button_for_back_to_all_lessons_day


def create_settings_profile_kb():
    settings_profile_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Заполнить заново',
                                  callback_data='edit_profile')],
            [InlineKeyboardButton(text='❌Удалить профиль❌',
                                  callback_data='delete_profile')],
            [InlineKeyboardButton(text='<назад',
                                  callback_data='auth_student')]
        ]
    )

    return settings_profile_kb


def create_information_penalties(students_penalty):
    #print(x.week_date for x in students_penalty.penalties)
    buttons = [
        [InlineKeyboardButton(text=f'{penalty.week_date} {penalty.lesson_on}'
                                   f' - {penalty.lesson_off}',
                              callback_data=PlugPenaltyStudentCallbackFactory(
                                  plug=''
                              ).pack())]
        for penalty in students_penalty.penalties
    ] + [[InlineKeyboardButton(text='<назад', callback_data='auth_student')]]

    information_penalties_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return information_penalties_kb
