from aiogram.fsm.state import State, StatesGroup


class FSMRegistrationTeacherForm(StatesGroup):
    fill_name = State()
    fill_surname = State()
    fill_phone = State()
    fill_bank = State()
    fill_penalty = State()


class FSMRegistrationLessonWeek(StatesGroup):
    fill_work_start = State()
    fill_work_end = State()


class FSMAddStudentToStudy(StatesGroup):
    fill_id = State()
