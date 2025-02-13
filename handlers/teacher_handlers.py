from datetime import date, datetime, timedelta, time
from pprint import pprint

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.requirements import command_add_teacher, command_add_lesson_week
from filters.filters import IsTeacherInDatabase, IsLessonWeekInDatabase, \
    FindNextSevenDaysFromKeyboard, IsCorrectTimeInput
from keyboards.repetitor_kb import create_entrance_kb, create_back_to_entrance_kb, create_authorization_kb, \
    show_next_seven_days_kb
from services.services import give_dict_with_days, create_date_record, create_time_record

router = Router()


class FSMRegistrationTeacherForm(StatesGroup):
    fill_name = State()
    fill_surname = State()


class FSMRegistrationLessonWeek(StatesGroup):
    fill_work_start = State()
    fill_work_end = State()


# session.merge()
@router.message(Command(commands='cancel'))
async def process_restart_state(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Состояние очищено!")


# @router.message((Command(commands='teacher_entrance') &
#                 StateFilter(default_state)) |
# #                 StateFilter(FSMAuthorizationTeacherForm.fill_ready))
# @router.message(lambda x: (x.text == 'teacher_entrance' and StateFilter(default_state)) or
#                           StateFilter(FSMAuthorizationTeacherForm.fill_ready)
#                 )

# @router.message(Command(commands='teacher_entrance'), StateFilter(default_state))
# async def process_entrance(message: Message):
#     teacher_entrance_kb = create_entrance_kb()
#     await message.answer(text='Вы попали в меню идентификации!',
#                          reply_markup=teacher_entrance_kb)

# Логика входа в меню идентификации
@router.message(Command(commands='teacher_entrance'), StateFilter(default_state))
async def process_entrance(message: Message):
    teacher_entrance_kb = create_entrance_kb()
    await message.answer(text='Меню идентификации!',
                         reply_markup=teacher_entrance_kb)


@router.callback_query(F.data == 'teacher_entrance')
async def process_entrance(callback: CallbackQuery):
    teacher_entrance_kb = create_entrance_kb()
    await callback.answer('Вы попали в меню идентификации!')
    await callback.message.answer(text='Меню идентификации',
                                  reply_markup=teacher_entrance_kb)
    print(callback.model_dump_json(indent=4))


# Логика регистрации учителя
@router.message(F.text == 'Регистрация', ~IsTeacherInDatabase(), StateFilter(default_state))
async def process_start_registration(message: Message, state: FSMContext):
    await message.answer(text="Пожалуйста, введите ваше имя!",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMRegistrationTeacherForm.fill_name)


@router.message(StateFilter(FSMRegistrationTeacherForm.fill_name), F.text.isalpha())
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text="Спасибо!\n\n А теперь введите фамилию!")
    await state.set_state(FSMRegistrationTeacherForm.fill_surname)


@router.message(StateFilter(FSMRegistrationTeacherForm.fill_name))
async def process_wrong_name_sent(message: Message):
    await message.answer(text='То, что вы отправили не похоже на имя(\n\n'
                              'Пожалуйста, введите ваше имя!')


@router.message(StateFilter(FSMRegistrationTeacherForm.fill_surname), F.text.isalpha())
async def process_surname_sent(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(surname=message.text)

    teacher_form = await state.get_data()
    await command_add_teacher(session,
                              message.from_user.id,
                              **teacher_form)
    await state.clear()

    await message.answer(text="Спасибо, что ввели данные!\n\n"
                              "Нажми на кнопку, чтобы вернуться!!!",
                         reply_markup=create_back_to_entrance_kb())


@router.message(StateFilter(FSMRegistrationTeacherForm.fill_surname))
async def process_wrong_surname_sent(message: Message):
    await message.answer(text='То, что вы отправили не похоже на фамилию('
                              'Пожалуйста, введите вашу фамилию!')


# Случай, когда учитель уже зарегестрирован, но нажал на кнопку регистрации!
@router.message(F.text == 'Регистрация', IsTeacherInDatabase())
async def process_not_start_registration(message: Message):
    await message.answer(text='Вы уже зарегестрированы!')


# @router.callback_query(F.text == 'Регистрация', IsTeacherInDatabase())
# async def process_not_start_registration(callback: CallbackQuery):
#     await callback.answer(text='Вы уже зарегестрированы!')

# Логика авторизации учителя

# Случай, когда учитель не зарегестрирован, но нажал на кнопку авторизации!
@router.message(F.text == 'Авторизация', ~IsTeacherInDatabase())
async def process_not_start_authorization(message: Message):
    await message.answer(text='Вы еще не зарегестрированы!')


# Зашли в профиль репетитора
@router.message(F.text == 'Авторизация', IsTeacherInDatabase())
async def process_start_authorization(message: Message):
    await message.answer(text='Вы успешно вошли в свой профиль!\n\n'
                              'В меню ниже выберите то, что хотите сделать)',
                         reply_markup=create_authorization_kb())


# Кнопка __расписание__ ->
@router.message(F.text == 'Расписание')
async def process_show_schedule(message: Message):
    next_seven_days = give_dict_with_days(datetime.now() + timedelta(days=1))

    await message.answer(text='Давайте поработаем с вашим расписанием\n'
                              'на 7 дней вперед!\n\n Чтобы заполнить, выбери день!',
                         reply_markup=show_next_seven_days_kb(**next_seven_days))


# Случай, когда день в расписании еще не заполнен, логика заполнения формы

@router.message(FindNextSevenDaysFromKeyboard(), ~IsLessonWeekInDatabase(), StateFilter(default_state))
async def process_create_day_schedule(message: Message, state: FSMContext):
    await message.answer(text="Вам надо будет ввести время начала и конца вашей работы!\n"
                              "Вводи данные в формате ЧАСЫ:МИНУТЫ\n(например, 09:33; 12:00\n\n"
                              "Давайте начнем!\n\n"
                              "Введите время начала вашей работы!"
                         )

    # format_date = create_date_record(message.txt)
    await state.update_data(week_date=message.text)

    await state.set_state(FSMRegistrationLessonWeek.fill_work_start)


@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), IsCorrectTimeInput())
async def process_time_start_sent(message: Message, state: FSMContext):
    # hour, minute = list(map(int, message.text.split(':')))
    await state.update_data(work_start=message.text)  # time(hour=hour, minute=minute))

    await state.set_state(FSMRegistrationLessonWeek.fill_work_end)
    await message.answer(text='Введите время, в которое вы заканчиваете работать!'
                              'Вводи данные в формате ЧАСЫ:МИНУТЫ (например, 09:33; 12:00')


@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsCorrectTimeInput())
async def process_not_time_start_sent(message: Message):
    await message.answer("Неправильно ввели время! Попробуйте еще раз!")


@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsCorrectTimeInput())
async def process_time_end_sent(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(work_end=message.text)  # time(hour=hour, minute=minute))
    lesson_day_form = await state.get_data()

    lesson_day_form['week_date'] = create_date_record(lesson_day_form['week_date'])
    lesson_day_form['work_start'] = create_time_record(lesson_day_form['work_start'])
    lesson_day_form['work_end'] = create_time_record(lesson_day_form['work_end'])

    await command_add_lesson_week(session,
                                  message.from_user.id,
                                  **lesson_day_form)

    await state.clear()


@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsCorrectTimeInput())
async def process_not_time_end_sent(message: Message):
    await message.answer("Неправильно ввели время! Попробуйте еще раз!")
