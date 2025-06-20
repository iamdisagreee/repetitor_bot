from datetime import date

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callback_factory.student_factories import ChangeStatusOfAddListCallbackFactory, DeleteStudentToStudyCallbackFactory
from bot.callback_factory.teacher_factories import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory, \
    DeleteDayCallbackFactory, ShowDaysOfScheduleTeacherCallbackFactory, ShowInfoDayCallbackFactory, \
    DeleteDayScheduleCallbackFactory, PlugPenaltyTeacherCallbackFactory, PlugScheduleLessonWeekDayBackFactory, \
    DebtorInformationCallbackFactory, RemoveDebtorFromListCallbackFactory, ShowNextSevenDaysCallbackFactory, \
    ScheduleEditTeacherCallbackFactory
from bot.lexicon.lexicon_teacher import LEXICON_TEACHER
from bot.services.services import NUMERIC_DATE

# ------------------------------------- НАСТРОЙКА ОПИСАНИЯ ----------------------------------------
def create_menu_description_teacher_kb():
    menu_description_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['lessons_week_teacher'],
                                  callback_data='description_lessons_week_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['management_students'],
                                  callback_data='description_management_students')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['settings_teacher'],
                                  callback_data='description_settings_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['notifications_teacher'],
                                  callback_data='description_notifications_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='start')
             ]
        ]
    )

    return menu_description_teacher_kb

def create_back_to_menu_settings_teacher_kb():
    back_to_menu_settings_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='help_teacher'),
            InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='start')]
        ]
    )
    return back_to_menu_settings_kb
# -------------------------------------------------------------------------------------------------
def create_entrance_kb():
    entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=LEXICON_TEACHER['authorization'],
                                                  callback_data='auth_teacher')],
                            [InlineKeyboardButton(text=LEXICON_TEACHER['registration'],
                                                  callback_data='reg_teacher')]
                        ] + [
                            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                                  callback_data='start')]
                        ]
    )
    return entrance_kb


def create_back_to_entrance_kb():
    back_to_entrance_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=LEXICON_TEACHER['go_menu_identification'],
                callback_data='teacher_entrance')
            ]
        ]
    )

    return back_to_entrance_kb


def create_authorization_kb():
    authorization_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['lessons_week_teacher'],
                                  callback_data='lessons_week_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['management_students'],
                                  callback_data='management_students')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['settings_teacher'],
                                  callback_data='settings_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='teacher_entrance')
             ]
        ]
    )
    return authorization_kb


# Отображаем клавиатуру на следующие 7 дней + сегодняшний день
def create_lessons_week_teacher_kb(days):
    lessons_week_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=
        [
            [InlineKeyboardButton(text=LEXICON_TEACHER['next_seven_days_kb']
                                  .format(cur_date.strftime("%d.%m"),
                                          NUMERIC_DATE[
                                              date(
                                                  year=cur_date.year,
                                                  month=cur_date.month,
                                                  day=cur_date.day
                                              ).isoweekday()
                                          ]
                                          ),
                                  callback_data=ShowNextSevenDaysCallbackFactory(
                                      week_date=str(cur_date)
                                  ).pack()
                                  )
             ]
            for cur_date in days
        ] + [[InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                   callback_data='auth_teacher')]]
    )
    return lessons_week_teacher_kb


# Отображает, что мы можем сделать с текущим днем
def create_config_teacher_kb(week_date: str):
    config_teacher_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=LEXICON_TEACHER['schedule_show'],
                                                  callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                                      week_date=week_date
                                                  ).pack()
                                                  )
                             ],
                            [InlineKeyboardButton(text=LEXICON_TEACHER['schedule_teacher'],
                                                  callback_data=ScheduleEditTeacherCallbackFactory(
                                                      week_date=week_date
                                                  ).pack()
                                                  )
                             ],
                            [InlineKeyboardButton(text=LEXICON_TEACHER['confirmation_pay'],
                                                  callback_data=ShowDaysOfPayCallbackFactory(
                                                      week_date=week_date
                                                  ).pack()
                                                  )
                             ],
                        ] + [
                            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                                  callback_data='lessons_week_teacher'),
                             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                                  callback_data='auth_teacher')
                             ]
                        ]
    )

    return config_teacher_kb

# Клавиатура кнопок __ДОБАВИТЬ__ и __УДАЛИТЬ__
def create_add_remove_gap_kb(week_date: str):
    add_remove_gap_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['add_gap_teacher'],
                                  callback_data='add_gap_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['remove_gap_teacher'],
                                  callback_data='remove_gap_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data=ShowNextSevenDaysCallbackFactory(
                                      week_date=week_date
                                  ).pack()
                                  ),
             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_teacher')
             ]
        ]
    )

    return add_remove_gap_kb


def create_back_to_profile_kb(time_to_repeat: str):
    buttons = [
        [InlineKeyboardButton(text=LEXICON_TEACHER['congratulations_edit_notices'],
                              callback_data=ScheduleEditTeacherCallbackFactory(
                                  week_date=time_to_repeat
                              ).pack()
                              )
         ],
    ]

    back_to_profile_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return back_to_profile_kb


def create_all_records_week_day(weeks_day,
                                week_date):
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
                      text=LEXICON_TEACHER['back'],
                      callback_data=ScheduleEditTeacherCallbackFactory(
                          week_date=week_date
                      ).pack()
                  )]
              ]
    all_records_week_day_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return all_records_week_day_kb


# Отображаем статусы занятий за день
# async def show_status_lesson_day_kb(cur_buttons,
#                                     session: AsyncSession,
#                                     week_date_str: str):
#     builder = InlineKeyboardBuilder()
#     res_buttons = []
#
#     for button in cur_buttons:
#         # Случай, когда кнопка пустая
#         if button['student_id'] is None:
#             continue
#         student = await give_student_by_student_id(session, button['student_id'])
#         price = student.price / 2 * len(button['list_status'])
#         status = '✅' if len(button['list_status']) == sum(button['list_status']) else '❌'
#         res_buttons.append(
#             InlineKeyboardButton(
#                 text=LEXICON_TEACHER['status_lesson_day_kb'].format(
#                     status, student.name, button['lesson_on'].strftime("%H:%M"),
#                     button['lesson_off'].strftime("%H:%M"), price),
#                 callback_data=EditStatusPayCallbackFactory(
#                     lesson_on=button['lesson_on'].strftime("%H:%M"),
#                     lesson_off=button['lesson_off'].strftime("%H:%M"),
#                     week_date=week_date_str,
#                 ).pack()
#             )
#         )
#     res_buttons.append(InlineKeyboardButton(text=LEXICON_TEACHER['back'],
#                              callback_data=ShowNextSevenDaysCallbackFactory(
#                                  week_date=week_date_str
#                              ).pack()
#                              )
#                        )
#     res_buttons.append(
#                 InlineKeyboardButton(text=LEXICON_TEACHER['home'],
#                              callback_data='auth_teacher')
#     )
#
#     builder.row(*res_buttons[:-2], width=1)
#     builder.row(*res_buttons[-2:], width=2)
#
#     return builder.as_markup()

async def show_status_lesson_day_kb(buttons,
                                    session: AsyncSession,
                                    week_date_str: str):
    builder = InlineKeyboardBuilder()
    res_buttons = []

    for button in buttons:
        if button['student'] is None:
            continue

        res_buttons.append(
            InlineKeyboardButton(
                text=LEXICON_TEACHER['status_lesson_day_kb'].format(
                    ['❌', '✅'][button['status']], button['student'], button['lesson_on'].strftime("%H:%M"),
                    button['lesson_off'].strftime("%H:%M"), button['price']),
                callback_data=EditStatusPayCallbackFactory(
                    lesson_on=button['lesson_on'].strftime("%H:%M"),
                    lesson_off=button['lesson_off'].strftime("%H:%M"),
                    week_date=week_date_str,
                ).pack()
            )
        )

    res_buttons.append(InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                             callback_data=ShowNextSevenDaysCallbackFactory(
                                 week_date=week_date_str
                             ).pack()
                             )
                       )
    res_buttons.append(
                InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                             callback_data='auth_teacher')
    )

    builder.row(*res_buttons[:-2], width=1)
    builder.row(*res_buttons[-2:], width=2)

    return builder.as_markup()

#
# def show_schedule_lesson_day_kb(cur_buttons,
#                                 week_date_str: str):
#     builder = InlineKeyboardBuilder()
#     res_buttons = []
#     for button in cur_buttons:
#         if button['list_status'] != [-1]:
#             status_bool = len(button['list_status']) == sum(button['list_status'])
#             status = LEXICON_TEACHER['paid'] if status_bool \
#                 else LEXICON_TEACHER['not_paid']
#             # student = await give_student_by_student_id(session, button['student_id'])
#             callback_data = ShowInfoDayCallbackFactory(
#                 lesson_on=button['lesson_on'].strftime("%H:%M"),
#                 lesson_off=button['lesson_off'].strftime("%H:%M"),
#                 week_date=week_date_str,
#                 status=status_bool,
#                 price=button['price'] / 2 * len(button['list_status'])
#             ).pack()
#         else:
#             status = LEXICON_TEACHER['not_reserved']
#             callback_data = PlugScheduleLessonWeekDayBackFactory(
#                 plug=button['lesson_on'].strftime("%H:%M")
#             ).pack()
#
#         res_buttons.append(
#             InlineKeyboardButton(
#                 text=LEXICON_TEACHER['text_schedule_lesson_day'].format(
#                     status, button['lesson_on'].strftime("%H:%M"),
#                     button['lesson_off'].strftime("%H:%M")
#                 ),
#                 callback_data=callback_data
#             )
#         )
#     res_buttons.append(
#         InlineKeyboardButton(text=LEXICON_TEACHER['back'],
#                              callback_data=ShowNextSevenDaysCallbackFactory(
#                                  week_date=week_date_str
#                              ).pack()
#                              )
#         )
#     res_buttons.append(
#         InlineKeyboardButton(text=LEXICON_TEACHER['home'],
#                                  callback_data='auth_teacher'),
#         )
#
#     builder.row(*res_buttons[:-2], width=1)
#     builder.row(*res_buttons[-2:], width=2)
#     return builder.as_markup()

def show_schedule_lesson_day_kb(buttons,
                                week_date_str: str):
    builder = InlineKeyboardBuilder()
    res_buttons = []

    for button in buttons:
        # print(button)
        if button['student'] is not None:
            status = ['❌', '✅'][button['status']]
            callback_data = ShowInfoDayCallbackFactory(
                lesson_on=button['lesson_on'].strftime("%H:%M"),
                lesson_off=button['lesson_off'].strftime("%H:%M"),
                week_date=week_date_str,
                status=button['status'],
                price=button['price']
            ).pack()
        else:
            status = LEXICON_TEACHER['not_reserved']
            callback_data = PlugScheduleLessonWeekDayBackFactory(
                plug=button['lesson_on'].strftime("%H:%M")
            ).pack()

        res_buttons.append(
            InlineKeyboardButton(
                text=LEXICON_TEACHER['text_schedule_lesson_day'].format(
                    status, button['lesson_on'].strftime("%H:%M"),
                    button['lesson_off'].strftime("%H:%M")
                ),
                callback_data=callback_data
            )
        )

    res_buttons.append(InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                             callback_data=ShowNextSevenDaysCallbackFactory(
                                 week_date=week_date_str
                             ).pack()
                             )
                       )
    res_buttons.append(
                InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                             callback_data='auth_teacher')
    )

    builder.row(*res_buttons[:-2], width=1)
    builder.row(*res_buttons[-2:], width=2)

    return builder.as_markup()


def back_to_show_or_delete_schedule_teacher(week_date_str,
                                            lesson_on,
                                            lesson_off,
                                            student_id: int):
    return InlineKeyboardMarkup(inline_keyboard=
    [
        [InlineKeyboardButton(text=LEXICON_TEACHER['delete'],
                              callback_data=DeleteDayScheduleCallbackFactory(
                                  week_date=week_date_str,
                                  lesson_on=lesson_on,
                                  lesson_off=lesson_off,
                                  student_id=student_id
                              ).pack()
                              )],
        [
        InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                 callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                     week_date=week_date_str
                                 ).pack()
                                 ),
        InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                 callback_data='auth_teacher'),
        ]
    ]
    )

def delete_remove_lesson_by_teacher():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['ok'],
                                  callback_data='remove_lesson_by_teacher'),]
        ]
    )

def back_to_show_schedule_teacher(week_date_str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                              callback_data=ShowDaysOfScheduleTeacherCallbackFactory(
                                  week_date=week_date_str
                              ).pack()
                              )
         ]
    ]
    )


# Клавиатура управления действиями
def settings_teacher_kb():
    settings_teacher = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['information_teacher'],
                                  callback_data='my_profile')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['notifications_teacher'],
                                  callback_data='notifications_teacher')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['registration_again'],
                                  callback_data='edit_profile')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['delete_profile'],
                                  callback_data='delete_profile')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='auth_teacher')]
        ]
    )

    return settings_teacher


def show_variants_edit_notifications_kb():
    variants_edit_notifications_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['until_time_notification_button'],
                                  callback_data='set_until_time_notification')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['daily_schedule_mailing_time_button'],
                                  callback_data='set_daily_schedule_mailing_time')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['daily_report_mailing_time_button'],
                                  callback_data='set_daily_report_mailing_time')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['daily_confirmation_notification'],
                                  callback_data='set_daily_confirmation_notification')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['cancellation_notification'],
                                  callback_data='set_cancellation_notification')],
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='settings_teacher'),
             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                  callback_data='auth_teacher')
             ]
        ]
    )
    return variants_edit_notifications_kb


def create_congratulations_edit_notifications_kb():
    notification_confirmation_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                  callback_data='notifications_teacher')]
        ]
    )
    return notification_confirmation_student_kb


def back_to_settings_kb():
    back_to_settings = [
        [
            InlineKeyboardButton(
                text=LEXICON_TEACHER['back'],
                callback_data='settings_teacher'),
            InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                 callback_data='auth_teacher')
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=back_to_settings)


# Клавиатура для выбора, что сделать с учениками!
def create_management_students_kb():
    buttons = [
        [InlineKeyboardButton(text=LEXICON_TEACHER['add_student'],
                              callback_data='allow_student')],
        [InlineKeyboardButton(text=LEXICON_TEACHER['list_added'],
                              callback_data='list_add_students')],
        [InlineKeyboardButton(text=LEXICON_TEACHER['list_debtors'],
                              callback_data='list_debtors')],
        [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                              callback_data='auth_teacher')]
    ]

    management_students_kb = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    return management_students_kb


# Клавиатура из всех учеников и их доступа к боту!
def create_list_add_students_kb(students):
    buttons = []
    for student in students:
        status_str = ['🔒', '🔑'][student.access.status]
        buttons.append([
            InlineKeyboardButton(text=LEXICON_TEACHER['list_added_students']
                                 .format(status_str, student.surname, student.name),
                                 callback_data=ChangeStatusOfAddListCallbackFactory(
                                     student_id=student.student_id
                                 ).pack())
        ]
        )
    buttons.append([InlineKeyboardButton(text=LEXICON_TEACHER['deleting'], callback_data='delete_student_by_teacher')])
    buttons.append([InlineKeyboardButton(text=LEXICON_TEACHER['back'], callback_data='management_students'),
                    InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                         callback_data='auth_teacher')
                    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_list_delete_students_kb(students):
    buttons = []
    for student in students:
        status_str = ['🔒', '🔑'][student.access.status]
        buttons.append([
            InlineKeyboardButton(text=f'{status_str} {student.surname} {student.name}',
                                 callback_data=DeleteStudentToStudyCallbackFactory(
                                     student_id=student.student_id
                                 ).pack())
        ]
        )
    buttons.append([InlineKeyboardButton(text=LEXICON_TEACHER['back'], callback_data='list_add_students'),
                    InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                         callback_data='auth_teacher')
                    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_back_to_management_students_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                              callback_data='management_students')]
    ])


# Клавиатура которая показывает всех учеников со штрафами
def show_list_of_debtors_kb(students):
    return InlineKeyboardMarkup(
        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text=LEXICON_TEACHER['information_debtors']
                                    .format(student.surname,
                                            student.name,
                                            len(student.penalties)),
                                    callback_data=PlugPenaltyTeacherCallbackFactory(
                                        plug=''
                                    ).pack())
                            ]
                            for student in students
                        ] + [
                            [InlineKeyboardButton(
                                text=LEXICON_TEACHER['back'],
                                callback_data='management_students')]
                        ]
    )


def create_notification_confirmation_student_kb():
    notification_confirmation_student_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=LEXICON_TEACHER['ok'],
                callback_data='notification_confirmation_student'
            )]
        ]
    )
    return notification_confirmation_student_kb


def create_list_debtors_kb(list_debtors):
    list_debtors_kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [
                                InlineKeyboardButton(text=LEXICON_TEACHER['line_debtor_information']
                                                     .format(debtor.week_date.strftime("%m.%d"),
                                                             debtor.student.name,
                                                             debtor.student.surname,
                                                             ),
                                                     callback_data=DebtorInformationCallbackFactory(
                                                         lesson_on=debtor.lesson_on.strftime("%H:%M"),
                                                         lesson_off=debtor.lesson_off.strftime("%H:%M"),
                                                         week_date=str(debtor.week_date),
                                                         amount_money=debtor.amount_money
                                                     ).pack()
                                                     )
                            ] for debtor in list_debtors
                        ] +
                        [
                            [InlineKeyboardButton(text=LEXICON_TEACHER['confirmation'],
                                                  callback_data='confirmation_debtors')],
                            [InlineKeyboardButton(text=LEXICON_TEACHER['back'],
                                                  callback_data='management_students'),
                             InlineKeyboardButton(text=LEXICON_TEACHER['home'],
                                                  callback_data='auth_teacher')
                             ]
                        ]
    )
    return list_debtors_kb


def change_list_debtors_kb(list_debtors):
    list_debtors = InlineKeyboardMarkup(
        inline_keyboard=[
                            [
                                InlineKeyboardButton(text=LEXICON_TEACHER['line_debtor_information']
                                                     .format(debtor.week_date.strftime("%m.%d"),
                                                             debtor.student.name,
                                                             debtor.student.surname,
                                                             ),
                                                     callback_data=RemoveDebtorFromListCallbackFactory(
                                                         debtor_id=str(debtor.debtor_id)
                                                     ).pack()
                                                     )
                            ] for debtor in list_debtors
                        ] + [
                            [InlineKeyboardButton(text=LEXICON_TEACHER['exit'],
                                                  callback_data='management_students')]
                        ]
    )
    return list_debtors
