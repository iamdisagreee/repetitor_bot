from uuid import UUID

from aiogram.filters.callback_data import CallbackData

from database import Student


class DeleteDayCallbackFactory(CallbackData, prefix='delete'):
    week_id: UUID


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

class DebtorInformationCallbackFactory(CallbackData, prefix='debtor', sep=';'):
    lesson_on: str
    lesson_off: str
    week_date: str
    amount_money: int