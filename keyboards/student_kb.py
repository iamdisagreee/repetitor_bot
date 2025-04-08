from datetime import date

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from callback_factory.student_factories import ExistFieldCallbackFactory, EmptyAddFieldCallbackFactory, \
    DeleteFieldCallbackFactory, EmptyRemoveFieldCallbackFactory, ShowDaysOfScheduleCallbackFactory, \
    StartEndLessonDayCallbackFactory, PlugPenaltyStudentCallbackFactory, InformationLessonCallbackFactory, \
    RemoveDayOfScheduleCallbackFactory
from callback_factory.teacher_factories import SentMessagePaymentStudentCallbackFactory, \
    ScheduleShowTeacherCallbackFactory, ShowInfoDayCallbackFactory, ShowDaysOfScheduleTeacherCallbackFactory
from lexicon.lexicon_student import LEXICON_STUDENT
from lexicon.lexicon_teacher import LEXICON_TEACHER
from services.services import NUMERIC_DATE


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
            [InlineKeyboardButton(text=LEXICON_STUDENT['show_schedule'],
                                  callback_data='show_schedule')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['settings_schedule'],
                                  callback_data='settings_schedule')],
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


def show_next_seven_days_settings_kb(*days):
    buttons = [
                  [InlineKeyboardButton(text=LEXICON_STUDENT['next_seven_days_kb']
                                        .format(cur_date.strftime("%d.%m"),
                                                NUMERIC_DATE[date(year=cur_date.year,
                                                                  month=cur_date.month,
                                                                  day=cur_date.day).isoweekday()]),
                                        callback_data=cur_date.strftime("%Y-%m-%d"))]
                  for cur_date in days
              ] + [[InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                         callback_data='auth_student')]]

    next_seven_days_with_cur_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return next_seven_days_with_cur_kb


def create_menu_add_remove_kb():
    add_remove_gap_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_STUDENT['add_gap_student'],
                                  callback_data='add_gap_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['remove_gap_student'],
                                  callback_data='remove_gap_student')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
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
    builder.button(text=LEXICON_STUDENT['exit'],
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


def all_lessons_for_day_kb(lessons):
    builder = InlineKeyboardBuilder()
    buttons = []
    for lesson in lessons:
        buttons.append(
            InlineKeyboardButton(
                text=LEXICON_STUDENT['all_lessons_for_day_kb']
                .format(lesson['start'].strftime("%H:%M"),
                        lesson['finished'].strftime("%H:%M")),
                callback_data=StartEndLessonDayCallbackFactory
                    (
                    lesson_on=lesson['start'].strftime("%H:%M"),
                    lesson_off=lesson['finished'].strftime("%H:%M")
                ).pack()
            )
        )
    buttons.append(InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                        callback_data='show_schedule')
                   )

    builder.row(*buttons, width=1)
    return builder.as_markup()


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
             ]
        ]
    )

    return button_for_back_to_all_lessons_day

def create_ok_remove_day_schedule_student_kb(week_date):
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
            [InlineKeyboardButton(text=LEXICON_STUDENT['registration_again'],
                                  callback_data='edit_profile')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['delete_profile'],
                                  callback_data='delete_profile')],
            [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                                  callback_data='auth_student')]
        ]
    )

    return settings_profile_kb


def create_back_to_settings_student_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_STUDENT['back'],
                              callback_data='settings_student')]
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

