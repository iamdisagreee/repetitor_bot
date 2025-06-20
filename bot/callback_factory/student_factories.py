# Фабрика коллбеков (существующую кнопки)
from datetime import time
from sys import prefix

from aiogram.filters.callback_data import CallbackData

class ShowNextSevenDaysStudentCallbackFactory(CallbackData, prefix='week_date', sep=';'):
    week_date: str

class ScheduleEditStudentCallbackFactory(CallbackData, prefix='edit', sep=';'):
    week_date: str

class ExistFieldCallbackFactory(CallbackData, prefix="time", sep='-'):
    lesson_start: str
    lesson_finished: str

# Фабрика колбеков (несуществующие кнопки)
class EmptyAddFieldCallbackFactory(CallbackData, prefix='plug'):
    plug: str


class DeleteFieldCallbackFactory(CallbackData, prefix='delete', sep=';'):
    lesson_start: str
    lesson_finished: str
    week_date: str

class EmptyRemoveFieldCallbackFactory(CallbackData, prefix='plug'):
    plug: str


class ShowDaysOfScheduleCallbackFactory(CallbackData, prefix='schedule'):
    week_date: str

class RemoveDayOfScheduleCallbackFactory(CallbackData, prefix='schedule', sep='.'):
    week_date: str
    lesson_on: str
    lesson_off: str

class StartEndLessonDayCallbackFactory(CallbackData, prefix='start_end_lesson', sep='-'):
    lesson_on: str
    lesson_off: str

class StartEndLessonDayWillFormedCallbackFactory(CallbackData, prefix='will_formed', sep=';'):
    week_date: str
    lesson_on: str
    lesson_off: str

class StartEndLessonDayFormedCallbackFactory(CallbackData, prefix='lesson_formed', sep=';'):
    week_date: str
    lesson_on: str
    lesson_off: str

class StartEndLessonDayNotFormedCallbackFactory(CallbackData, prefix='lesson_not_formed', sep=';'):
    week_date: str
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

class InformationLessonCallbackFactory(CallbackData, prefix='a', sep=';'):
    week_date: str
    lesson_on: str
    lesson_off: str
    full_price: int

