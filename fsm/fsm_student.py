from aiogram.fsm.state import State, StatesGroup


class FSMRegistrationStudentForm(StatesGroup):
    fill_name = State()
    fill_surname = State()
    fill_city = State()
    fill_place_study = State()
    fill_level = State()
    fill_level_class = State()
    fill_level_course = State()
    fill_subject = State()
    fill_teacher = State()
    fill_price = State()