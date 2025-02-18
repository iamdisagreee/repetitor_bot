from aiogram.filters.callback_data import CallbackData

from database import Student


class DeleteDayCallbackFactory(CallbackData, prefix='delete'):
    week_id: int


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


# class ShowDeleteLessonCallbackFactory(CallbackData, prefix='delete_days'):
#     week_date: str


class DeleteDayScheduleCallbackFactory(CallbackData, prefix='delete_day', sep='&'):
    lesson_on: str
    lesson_off: str
    week_date: str
