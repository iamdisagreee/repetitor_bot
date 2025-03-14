from aiogram.filters.callback_data import CallbackData


class InformationLessonWithDeleteCallbackFactory(CallbackData, prefix='b', sep=';'):
    week_date: str
    lesson_on: str
    lesson_off: str
    full_price: int