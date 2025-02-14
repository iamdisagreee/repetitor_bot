from datetime import date, datetime, timedelta, time
from pprint import pprint

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.requirements import command_add_teacher, command_add_lesson_week, give_installed_lessons_week, \
    delete_week_day
from filters.filters import IsTeacherInDatabase, IsLessonWeekInDatabaseCallback, \
    FindNextSevenDaysFromKeyboard, IsCorrectFormatInput, IsNoEndBiggerStart, IsDifferenceThirtyMinutes, \
    IsNoConflictWithStart, IsNoConflictWithEnd, IsRemoveNameRight, IsLessonWeekInDatabaseState
from keyboards.repetitor_kb import create_entrance_kb, create_back_to_entrance_kb, create_authorization_kb, \
    show_next_seven_days_kb, create_back_to_profile_kb, create_add_remove_gap_kb, create_all_records_week_day
from services.services import give_list_with_days, give_time_format_fsm, give_date_format_fsm, \
    give_list_registrations_str

router = Router()


class FSMRegistrationTeacherForm(StatesGroup):
    fill_name = State()
    fill_surname = State()


class FSMRegistrationLessonWeek(StatesGroup):
    fill_work_start = State()
    fill_work_end = State()


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

############################### Логика входа в меню идентификации #######################################
@router.callback_query(F.data == 'teacher_entrance', StateFilter(default_state))
async def process_entrance(callback: CallbackQuery):
    teacher_entrance_kb = create_entrance_kb()
    await callback.message.edit_text(text='Меню идентификации!',
                                     reply_markup=teacher_entrance_kb)

#################################### Логика регистрации учителя #####################################
@router.callback_query(F.data == 'reg_teacher', ~IsTeacherInDatabase(), StateFilter(default_state))
async def process_start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Пожалуйста, введите ваше имя!",
                                     )
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
@router.callback_query(F.data == 'reg_teacher', IsTeacherInDatabase())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer(text='Вы уже зарегестрированы!')


# @router.callback_query(F.text == 'Регистрация', IsTeacherInDatabase())
# async def process_not_start_registration(callback: CallbackQuery):
#     await callback.answer(text='Вы уже зарегестрированы!')

# Логика авторизации учителя

# Случай, когда учитель не зарегестрирован, но нажал на кнопку авторизации!
@router.callback_query(F.data == 'auth_teacher', ~IsTeacherInDatabase())
async def process_not_start_authorization(message: Message):
    await message.answer(text='Вы еще не зарегестрированы!')


###################################### Зашли в профиль репетитора #######################################
@router.callback_query(F.data == 'auth_teacher', IsTeacherInDatabase())
async def process_start_authorization(callback: CallbackQuery):
    await callback.message.edit_text(text='Вы успешно вошли в свой профиль!\n\n'
                                          'В меню ниже выберите то, что хотите сделать)',
                                     reply_markup=create_authorization_kb())


# Кнопка __расписание__ -> Добавление, Удаление
@router.callback_query(F.data == 'schedule_teacher')
async def process_show_schedule(callback: CallbackQuery):
    next_seven_days = give_list_with_days(datetime.now() + timedelta(days=1))

    await callback.message.edit_text(text='Давайте поработаем с вашим расписанием\n'
                                          'на 7 дней вперед!\n\n Чтобы заполнить, выбери день!',
                                     reply_markup=show_next_seven_days_kb(*next_seven_days, back='<<назад'))


# @router.callback_query(F.data == 'schedule_teacher')
# async def process_menu_add_remove(callback: CallbackQuery):
#     await callback.message.edit_text(text='Выберите что вы хотите сделать с раписанием!',
#                                      reply_markup=create_add_remove_gap_kb(back='<<назад'))


# Кнопка добавить расписание
# @router.callback_query(F.data == 'add_gap_teacher')
# async def process_add_gap_teacher(callback: CallbackQuery):
#     next_seven_days = give_list_with_days(datetime.now() + timedelta(days=1))
#     await callback.message.edit_text(text='Давайте поработаем с вашим расписанием\n'
#                                           'на 7 дней вперед!\n\n Чтобы заполнить, выбери день!',
#                                      reply_markup=show_next_seven_days_kb(*next_seven_days, back='<<назад'))


# Выбираем кнопку __добавить__ или __удалить__ окошко!!
@router.callback_query(FindNextSevenDaysFromKeyboard())
async def process_menu_add_remove(callback: CallbackQuery, state: FSMContext):
    await state.update_data(week_date=callback.data)

    await callback.message.edit_text(text='Выберите что вы хотите сделать с раписанием!',
                                     reply_markup=create_add_remove_gap_kb(back='<<назад'))


########################## Случай, когда сработала кнока __добавить__! ######################################
@router.callback_query(F.data == 'add_gap_teacher', StateFilter(default_state))
async def process_create_day_schedule(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Вам надо будет ввести время начала и конца вашей работы!\n"
                                       "Вводи данные в формате ЧАСЫ:МИНУТЫ\n(например, 09:33; 12:00\n\n"
                                       "Давайте начнем!\n\n"
                                       "Введите время начала вашей работы!"
                                  )
    # format_date = create_date_record(message.txt)
    await state.set_state(FSMRegistrationLessonWeek.fill_work_start)

    await callback.answer()


# Начинаем заполнять форму для вставки времени в базу данных
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), IsCorrectFormatInput(),
                IsNoConflictWithStart())
async def process_time_start_sent(message: Message, state: FSMContext):
    # hour, minute = list(map(int, message.text.split(':')))
    await state.update_data(work_start=message.text)  # time(hour=hour, minute=minute))

    await state.set_state(FSMRegistrationLessonWeek.fill_work_end)
    await message.answer(text='Введите время, в которое вы заканчиваете работать!'
                              'Вводи данные в формате ЧАСЫ:МИНУТЫ (например, 09:33; 12:00')


@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsCorrectFormatInput())
async def process_not_correct_format_start(message: Message):
    await message.answer("Неправильно ввели время! Попробуйте еще раз!")


# Случай, когда стартовое время уже лежит в заданном диапазоне
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsNoConflictWithStart())
async def process_start_in_range(message: Message, session: AsyncSession, state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    res_time = await give_installed_lessons_week(session,
                                                 message.from_user.id,
                                                 week_date)

    res_time_str = give_list_registrations_str(res_time)
    await message.answer('Стартовое время конфликтует с существующим!\n\n'
                         'Существующие записи:\n' + res_time_str +
                         '\n\nПопробуйте еще раз!')


# Случай успешного ввода времени
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsCorrectFormatInput(),
                IsDifferenceThirtyMinutes(), IsNoEndBiggerStart(), IsNoConflictWithEnd())
async def process_time_end_sent(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(work_end=message.text)  # time(hour=hour, minute=minute))
    lesson_day_form = await state.get_data()

    time_to_repeat = lesson_day_form['week_date']

    lesson_day_form['week_date'] = give_date_format_fsm(lesson_day_form['week_date'])
    lesson_day_form['work_start'] = give_time_format_fsm(lesson_day_form['work_start'])
    lesson_day_form['work_end'] = give_time_format_fsm(lesson_day_form['work_end'])

    await command_add_lesson_week(session,
                                  message.from_user.id,
                                  **lesson_day_form)

    await state.clear()

    await message.answer(text='Ваша анкета успешно сохранена!',
                         reply_markup=create_back_to_profile_kb(time_to_repeat)
                         )


# Cлучай, когда формат 00:00 не соблюдается
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsCorrectFormatInput())
async def process_not_correct_format(message: Message):
    await message.answer(text="Неправильно ввели время! Попробуйте еще раз!\n"
                              "формат ЧАСЫ:МИНУТЫ",
                         )


# Случай, когда время работы меньше 30 минут
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsDifferenceThirtyMinutes())
async def process_not_thirty_difference(message: Message):
    await message.answer("Время работы меньше 30 минут!\nВведите заново конец занятия!"
                         "Время старта заняий: ...")


# Случай, если время конца работы начинается раньше времени старта работы
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsNoEndBiggerStart())
async def process_not_thirty_difference(message: Message):
    await message.answer("Время конца работы меньше времени старта занятий!\nВведите заново!"
                         "Время старта занятий: ...")


# Случай, когда время конца занятий уже лежит в заданном диапазоне
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsNoConflictWithEnd())
async def process_start_in_range(message: Message, session: AsyncSession, state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    res_time = await give_installed_lessons_week(session,
                                                 message.from_user.id,
                                                 week_date)
    res_time_str = give_list_registrations_str(res_time)
    await message.answer('Конечное время конфликтует с существующим!\n\n'
                         'Существующие записи:\n' + res_time_str +
                         '\n\nПопробуй еще раз!')


########################## Случай, когда сработала кнока __удалить__! ######################################
@router.callback_query(F.data == 'remove_gap_teacher', IsLessonWeekInDatabaseState(), StateFilter(default_state))
async def process_create_day_schedule_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    weeks_days = await give_installed_lessons_week(session,
                                                   callback.from_user.id,
                                                   week_date)

    await callback.message.edit_text(text='Чтобы удалить, нажми на желаемую кнопку!',
                                     reply_markup=create_all_records_week_day(weeks_days))


# Проверяем, что апдейт содержит F.data об удаляемой информации: 'del_record_teacher_{week_day.week_id}'
@router.callback_query(IsRemoveNameRight())
async def process_delete_week_day(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    week_id = int(callback.data[-1])
    await delete_week_day(session,
                          week_id)

    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    weeks_days = await give_installed_lessons_week(session,
                                                   callback.from_user.id,
                                                   week_date)

    await callback.message.edit_text(text='Чтобы удалить, нажми на желаемую кнопку!',
                                     reply_markup=create_all_records_week_day(weeks_days))


# Случай, когда время еще не установлено в дне!
@router.callback_query(F.data == 'remove_gap_teacher', ~IsLessonWeekInDatabaseState())
async def process_create_day_schedule_nothing(callback: CallbackQuery):
    await callback.answer(text='Еще не установлено расписание!')
