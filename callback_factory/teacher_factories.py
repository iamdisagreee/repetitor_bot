import uuid
from sys import prefix
from uuid import UUID

from aiogram.filters.callback_data import CallbackData

from database import Student


class DeleteDayCallbackFactory(CallbackData, prefix='delete'):
    week_id: UUID

class ShowNextSevenDaysCallbackFactory(CallbackData, prefix='week_date',sep=';'):
    week_date: str

class ScheduleEditTeacherCallbackFactory(CallbackData, prefix='edit', sep=';'):
    week_date: str

class ScheduleShowTeacherCallbackFactory(CallbackData, prefix='show', sep=';'):
    week_date: str

class SettingsPayTeacherCallbackFactory(CallbackData, prefix='pay', sep=';'):
    week_date: str


class ShowDaysOfPayCallbackFactory(CallbackData, prefix='pay'):
    week_date: str


class EditStatusPayCallbackFactory(CallbackData, prefix='status_pay', sep='&'):
    lesson_on: str
    lesson_off: str
    week_date: str


class ShowDaysOfScheduleTeacherCallbackFactory(CallbackData, prefix='schedule_now', sep=':'):
    week_date: str


class ShowInfoDayCallbackFactory(CallbackData, prefix='show_day', sep='&'):
    lesson_on: str
    lesson_off: str
    week_date: str
    status: bool
    price: float


# Затычка для промежутков, которые еще не выбрал ученик
class PlugScheduleLessonWeekDayBackFactory(CallbackData, prefix='plug_day', sep='-'):
    plug: str


class DeleteDayScheduleCallbackFactory(CallbackData, prefix='delete_day', sep='&'):
    lesson_on: str
    lesson_off: str
    week_date: str


class PlugPenaltyTeacherCallbackFactory(CallbackData, prefix='plug'):
    plug: str

class SentMessagePaymentStudentCallbackFactory(CallbackData, prefix='sent',  sep=';'):
    student_id: int
    week_date: str
    lesson_on: str
    lesson_off: str

class SentMessagePaymentStudentDebtorCallbackFactory(CallbackData, prefix='sent_debtor',  sep=';'):
    student_id: int
    week_date: str
    lesson_on: str
    lesson_off: str

class DebtorInformationCallbackFactory(CallbackData, prefix='debtor', sep=';'):
    lesson_on: str
    lesson_off: str
    week_date: str
    amount_money: int

class RemoveDebtorFromListCallbackFactory(CallbackData, prefix='delete', sep=','):
    debtor_id: str