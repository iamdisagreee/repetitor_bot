from aiogram.filters.callback_data import CallbackData


class ShowDaysOfPayCallbackFactory(CallbackData, prefix='pay'):
    week_date: str