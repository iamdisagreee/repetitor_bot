# Фабрика коллбеков (существующую кнопки)
from datetime import time

from aiogram.filters.callback_data import CallbackData


class ExistFieldCallbackFactory(CallbackData, prefix="time", sep='-'):
    lesson_start: str
    lesson_end: str


# Фабрика колбеков (несуществующие кнопки)
class NotExistFieldCallbackFactory(CallbackData, prefix='plug'):
    plug: str
