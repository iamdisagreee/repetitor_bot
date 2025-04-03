from aiogram.fsm.state import State, StatesGroup


class FSMRegistrationTeacherForm(StatesGroup):
    fill_name = State()
    fill_surname = State()
    fill_phone = State()
    fill_bank = State()
    fill_penalty = State()
    fill_until_time_notification = State()
    fill_daily_schedule_mailing_time = State()
    fill_daily_report_mailing_time = State()
    fill_days_cancellation_notification = State()


class FSMRegistrationLessonWeek(StatesGroup):
    fill_work_start = State()
    fill_work_end = State()


class FSMAddStudentToStudy(StatesGroup):
    fill_id = State()
