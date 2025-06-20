from datetime import date

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callback_factory.student_factories import ExistFieldCallbackFactory, EmptyAddFieldCallbackFactory, \
    DeleteFieldCallbackFactory, EmptyRemoveFieldCallbackFactory, ShowDaysOfScheduleCallbackFactory, \
    StartEndLessonDayCallbackFactory, PlugPenaltyStudentCallbackFactory, InformationLessonCallbackFactory, \
    RemoveDayOfScheduleCallbackFactory, ShowNextSevenDaysStudentCallbackFactory, ScheduleEditStudentCallbackFactory, \
    StartEndLessonDayFormedCallbackFactory, StartEndLessonDayNotFormedCallbackFactory, \
    StartEndLessonDayWillFormedCallbackFactory
from bot.callback_factory.taskiq_factories import InformationLessonWithDeleteCallbackFactory
from bot.callback_factory.teacher_factories import SentMessagePaymentStudentCallbackFactory, \
    ShowDaysOfScheduleTeacherCallbackFactory, \
    SentMessagePaymentStudentDebtorCallbackFactory
from bot.lexicon.lexicon_student import LEXICON_STUDENT
from bot.lexicon.lexicon_teacher import LEXICON_TEACHER
from bot.services.services import NUMERIC_DATE

# ------------------------------------- НАСТРОЙКА ОПИСАНИЯ ----------------------------------------
def create_menu_description_student_kb():
    menu_description_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['lessons_student'],
                                  callback_data='description_lessons_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['penalties'],
                                  callback_data='description_penalties_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['debts'],
                                  callback_data='description_debts_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['settings_student'],
                                  callback_data='description_settings_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['notifications_student'],
                                  callback_data='description_notifications_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data='start')]
        ]
    )
    return menu_description_student_kb

def create_back_to_menu_settings_student_kb():
    back_to_menu_settings_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data='help_student'),
            InlineKeyboardButton(text=LEXICON_STUDENT['home'],
                                  callback_data='start')]
        ]
    )
    return back_to_menu_settings_kb
# --------------------------------------------------------------------------------------------
def create_entrance_kb():
    entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=LEXICON_STUDENT['authorization'],
                                                  callback_data='auth_student')],
                            [InlineKeyboardButton(text=LEXICON_STUDENT['registration'],
                                                  callback_data='reg_student')]
                        ] + [
                            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                                  callback_data='start')]
                        ]
    )
    return entrance_kb


def create_level_choice_kb():
    level_choice_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LEXICON_STUDENT['course_learning']),
             KeyboardButton(text=LEXICON_STUDENT['class_learning'])]
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
            text=LEXICON_STUDENT['go_menu_identification'],
            callback_data='student_entrance')]]
    )

    return back_to_entrance_kb


def create_authorization_kb():
    authorization_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['lessons_student'],
                                  callback_data='lessons_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['penalties'],
                                  callback_data='penalties')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['debts'],
                                  callback_data='debts')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['settings_student'],
                                  callback_data='settings_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data='student_entrance')]
        ],
    )
    return authorization_kb


def show_next_seven_days_student_kb(days):
    buttons = [
                  [InlineKeyboardButton(text=LEXICON_STUDENT['next_seven_days_kb']
                                        .format(cur_date.strftime("%d.%m"),
                                                NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]),
                                        callback_data=ShowNextSevenDaysStudentCallbackFactory(
                                            week_date=str(cur_date)
                                        ).pack()
                                        )
                   ]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                         callback_data='auth_student')]]
    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return next_seven_days_with_cur_kb


def create_config_student_kb(week_date: str):
    config_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['show_schedule'],
                                  callback_data=ShowDaysOfScheduleCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  )
             ],
            [InlineKeyboardButton(text=LEXICON_STUDENT['settings_schedule'],
                                  callback_data=ScheduleEditStudentCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  )
             ],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                   callback_data='lessons_student'
                                  ),
            InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_student')
            ]
        ]
    )
    return config_student_kb


def create_menu_add_remove_kb(week_date):
    add_remove_gap_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['add_gap_student'],
                                  callback_data='add_gap_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['remove_gap_student'],
                                  callback_data='remove_gap_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data=ShowNextSevenDaysStudentCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  ),
             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_student')
             ]
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
                text=LEXICON_STUDENT['free_slot']
                .format(lesson['lesson_start'].strftime("%H:%M"),
                        lesson['lesson_end'].strftime("%H:%M")),
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

    builder.button(text=LEXICON_STUDENT['move_left'],
                   callback_data='move_left_add')
    builder.button(text=LEXICON_STUDENT['move_right'],
                   callback_data='move_right_add')
    builder.button(text=LEXICON_STUDENT['back'],
                   callback_data=ScheduleEditStudentCallbackFactory(
                       week_date=week_date_str
                   ).pack()
                   )

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
                lesson_finished=lesson.lesson_finished.strftime("%H:%M"),
                week_date=week_date_str
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

    builder.button(text=LEXICON_STUDENT['move_left'],
                   callback_data='move_left_remove')
    builder.button(text=LEXICON_STUDENT['move_right'],
                   callback_data='move_right_remove')
    builder.button(text=LEXICON_STUDENT['back'],
                   callback_data=ScheduleEditStudentCallbackFactory(
                       week_date=week_date_str
                   ).pack()
                   )

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def show_next_seven_days_schedule_kb(*days):
    buttons = [
                  [InlineKeyboardButton(
                      text=LEXICON_STUDENT['next_seven_days_schedule_student_kb']
                      .format(cur_date.strftime("%d.%m"),
                              NUMERIC_DATE[date(year=cur_date.year,
                                                month=cur_date.month,
                                                day=cur_date.day).isoweekday()]),
                      callback_data=ShowDaysOfScheduleCallbackFactory(
                          week_date=cur_date.strftime("%Y-%m-%d")
                      ).pack()
                  )
                  ]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                         callback_data='auth_student')]]

    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    return next_seven_days_with_cur_kb


def all_lessons_for_day_kb(lessons, week_date):
    builder = InlineKeyboardBuilder()
    buttons = []
    variants = ['❔', '📋']
    for lesson in lessons:
        is_formed = lesson['count_gaps'] == lesson['count_is_formed']
        text=LEXICON_STUDENT['all_lessons_for_day_kb']\
                .format(variants[is_formed],
                        lesson['start'].strftime("%H:%M"),
                        lesson['finished'].strftime("%H:%M"))

        if is_formed:
            buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=StartEndLessonDayCallbackFactory
                        (
                        lesson_on=lesson['start'].strftime("%H:%M"),
                        lesson_off=lesson['finished'].strftime("%H:%M")
                    ).pack()
                )
            )
        else:
            buttons.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=StartEndLessonDayWillFormedCallbackFactory(
                        week_date=str(week_date),
                        lesson_on=lesson['start'].strftime("%H:%M"),
                        lesson_off=lesson['finished'].strftime("%H:%M")
                    ).pack()
                )
            )
    buttons.append(InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                        callback_data=ShowNextSevenDaysStudentCallbackFactory(
                                            week_date=str(week_date)
                                        ).pack()
                                        ),
                   )
    buttons.append(InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                    callback_data='auth_student'))

    builder.row(*buttons[:-2], width=1)
    builder.row(*buttons[-2:], width=2)

    return builder.as_markup()

def is_form_lesson_kb(week_date,
                    lesson_on,
                    lesson_off):
    form_lesson_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['yes'],
                                  callback_data=StartEndLessonDayFormedCallbackFactory(
                                      week_date=week_date,
                                      lesson_on=lesson_on,
                                      lesson_off=lesson_off
                                  ).pack()
                                  )],
            [InlineKeyboardButton(text=LEXICON_STUDENT['no'],
                                  callback_data=StartEndLessonDayNotFormedCallbackFactory(
                                      week_date=week_date,
                                      lesson_on=lesson_on,
                                      lesson_off=lesson_off
                                  ).pack()
                                  )],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data=ShowDaysOfScheduleCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  ),
             InlineKeyboardButton(text=LEXICON_STUDENT['home'],
                                  callback_data='auth_student')]
        ]
    )
    return form_lesson_kb

def create_button_for_back_to_all_lessons_day(week_date_str,
                                              student,
                                              lesson_on,
                                              lesson_off,
                                              counter_lessons
                                              ):
    button_for_back_to_all_lessons_day = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['confirm_lesson'],
                                  callback_data=InformationLessonCallbackFactory(
                                      week_date=week_date_str,
                                      lesson_on=lesson_on,
                                      lesson_off=lesson_off,
                                      full_price=student.price * counter_lessons / 2
                                  ).pack()
                                  )
             ],
            [InlineKeyboardButton(text=LEXICON_STUDENT['cancel'],
                                  callback_data=RemoveDayOfScheduleCallbackFactory(
                                      week_date=week_date_str,
                                      lesson_on=lesson_on,
                                      lesson_off=lesson_off
                                  ).pack()
                                  )
             ],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data=ShowDaysOfScheduleCallbackFactory(
                                      week_date=week_date_str
                                  ).pack()
                                  )
             ,
             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_student')
             ]
        ]
    )
    return button_for_back_to_all_lessons_day

def create_button_for_back_to_all_lessons_not_formed_day(week_date_str):
    button_for_back_to_all_lessons_day = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data=ShowDaysOfScheduleCallbackFactory(
                                      week_date=week_date_str
                                  ).pack()
                                  )
             ,
             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_student')
            ]
        ]
    )

    return button_for_back_to_all_lessons_day

def create_ok_show_day_schedule_student_kb(week_date):
    ok_remove_day_schedule_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['to_schedule'],
                                  callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  )
             ],
            [InlineKeyboardButton(text=LEXICON_STUDENT['ok'],
                                  callback_data='ok_remove_day_schedule_student')]
        ]
    )
    return ok_remove_day_schedule_student_kb


def create_settings_profile_kb():
    settings_profile_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['information_student'],
                                  callback_data='my_profile_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['notifications_student'],
                                  callback_data='notifications_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['registration_again'],
                                  callback_data='edit_profile')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['delete_profile'],
                                  callback_data='delete_profile')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data='auth_student')]
        ]
    )

    return settings_profile_kb

def show_variants_edit_notifications_student_kb():
    variants_edit_notifications_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['until_time_notification_button'],
                                  callback_data='set_until_time_notification')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='settings_student'),
             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_student')
             ]
        ]
    )
    return variants_edit_notifications_kb


def create_congratulations_edit_notifications_student_kb():
    notification_confirmation_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='notifications_student')]
        ]
    )
    return notification_confirmation_student_kb
def create_back_to_settings_student_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                              callback_data='settings_student'),
         InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                              callback_data='auth_student')
         ]
    ])


def create_information_penalties(student_penalties):
    buttons = [
                  [InlineKeyboardButton(text=LEXICON_STUDENT['information_penalty']
                                        .format(penalty.week_date, penalty.lesson_on,
                                                penalty.lesson_off),
                                        callback_data=PlugPenaltyStudentCallbackFactory(
                                            plug=''
                                        ).pack())]
                  for penalty in student_penalties
              ] + [[InlineKeyboardButton(text=LEXICON_STUDENT['back'], callback_data='auth_student')]]

    information_penalties_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return information_penalties_kb


def create_confirm_payment_teacher_kb(student_id: int,
                                      callback_data: InformationLessonCallbackFactory):
    confirm_payment_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=LEXICON_STUDENT['confirm_payment_student'],
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

def create_confirm_payment_teacher_by_debtor_kb(student_id: int,
                                      callback_data: InformationLessonWithDeleteCallbackFactory):
    # print('Попал в клавиатуру')
    confirm_payment_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=LEXICON_STUDENT['confirm_payment_student'],
                callback_data=SentMessagePaymentStudentDebtorCallbackFactory(
                    student_id=student_id,
                    week_date=callback_data.week_date,
                    lesson_on=callback_data.lesson_on,
                    lesson_off=callback_data.lesson_off
                ).pack()
            )]
        ]
    )

    return confirm_payment_teacher_kb

def create_debts_student_kb(list_debts):
    debts_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=LEXICON_STUDENT['debt_information']
                                                  .format(debt.week_date.strftime("%m.%d"),
                                                          debt.lesson_on.strftime("%H:%M"),
                                                          debt.lesson_off.strftime("%H:%M"),
                                                          debt.amount_money),
                                                  callback_data='debt_information')]
                            for debt in list_debts
                        ] + [
                            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                                  callback_data='auth_student')]
                        ]
    )

    return debts_student_kb
