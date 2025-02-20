# Фабрика коллбеков (существующую кнопки)
from datetime import time

from aiogram.filters.callback_data import CallbackData


class ExistFieldCallbackFactory(CallbackData, prefix="time", sep='-'):
    lesson_start: str
    lesson_finished: str


# Фабрика колбеков (несуществующие кнопки)
class EmptyAddFieldCallbackFactory(CallbackData, prefix='plug'):
    plug: str


class DeleteFieldCallbackFactory(CallbackData, prefix='delete', sep='-'):
    lesson_start: str
    lesson_finished: str


class EmptyRemoveFieldCallbackFactory(CallbackData, prefix='plug'):
    plug: str


class ShowDaysOfScheduleCallbackFactory(CallbackData, prefix='schedule'):
    week_date: str


class StartEndLessonDayCallbackFactory(CallbackData, prefix='start_end_lesson', sep='-'):
    lesson_on: str
    lesson_off: str


class ChangeStatusOfAddListCallbackFactory(CallbackData, prefix='change_status'):
    student_id: int


class AddStudentToStudyCallbackFactory(CallbackData, prefix='add_student'):
    student_id: int


class DeleteStudentToStudyCallbackFactory(CallbackData, prefix='delete_student'):
    student_id: int


class PlugPenaltyStudentCallbackFactory(CallbackData, prefix='plug'):
    plug: str
