from datetime import date, datetime, timedelta, time
from pprint import pprint

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from callback_factory.teacher import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory, \
    DeleteDayCallbackFactory, ShowDaysOfScheduleTeacherCallbackFactory, ShowInfoDayCallbackFactory, \
    DeleteDayScheduleCallbackFactory
from database.teacher_requirements import command_add_teacher, command_add_lesson_week, give_installed_lessons_week, \
    delete_week_day, give_all_lessons_day_by_week_day, change_status_pay_student, \
    give_information_of_one_lesson, delete_lesson
from filters.teacher_filters import IsTeacherInDatabase, IsLessonWeekInDatabaseCallback, \
    FindNextSevenDaysFromKeyboard, IsCorrectFormatInput, IsNoEndBiggerStart, IsDifferenceThirtyMinutes, \
    IsNoConflictWithStart, IsNoConflictWithEnd, IsRemoveNameRight, IsLessonWeekInDatabaseState, IsSomethingToConfirm
from keyboards.teacher_kb import create_entrance_kb, create_back_to_entrance_kb, create_authorization_kb, \
    show_next_seven_days_kb, create_back_to_profile_kb, create_add_remove_gap_kb, create_all_records_week_day, \
    show_next_seven_days_pay_kb, show_status_lesson_day_kb, show_next_seven_days_schedule_teacher_kb, \
    show_schedule_lesson_day_kb, back_to_show_schedule_teacher, back_to_show_or_delete_schedule_teacher
from services.services import give_list_with_days, give_time_format_fsm, give_date_format_fsm, \
    give_list_registrations_str, show_intermediate_information_lesson_day_status, give_result_info

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
    next_seven_days_with_cur = give_list_with_days(datetime.now())

    await callback.message.edit_text(text='Давайте поработаем с вашим расписанием\n'
                                          'на 7 дней вперед!\n\n Чтобы заполнить, выбери день!',
                                     reply_markup=show_next_seven_days_kb(*next_seven_days_with_cur, back='<<назад'))


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


# Проверяем, что кнопка с датой нажата и удаляем
@router.callback_query(DeleteDayCallbackFactory.filter())
async def process_delete_week_day(callback: CallbackQuery, session: AsyncSession, state: FSMContext,
                                  callback_data: DeleteDayCallbackFactory):
    week_id = callback_data.week_id
    await delete_week_day(session,
                          week_id)

    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    weeks_days = await give_installed_lessons_week(session,
                                                   callback.from_user.id,
                                                   week_date)

    await callback.message.edit_text(text='Чтобы удалить, нажми на желаемую кнопку!',
                                     reply_markup=create_all_records_week_day(weeks_days))


# Случай, когда нечего удалять из созданных промежутков!
@router.callback_query(F.data == 'remove_gap_teacher', ~IsLessonWeekInDatabaseState())
async def process_create_day_schedule_nothing(callback: CallbackQuery):
    await callback.answer(text='Еще не установлено расписание!')


########################### Кнопка __Подтверждение оплаты__ ########################
# Предоставляем выбор дат для просмотра оплаты
@router.callback_query(F.data == 'confirmation_pay')
async def process_confirmation_pay(callback: CallbackQuery):
    next_seven_days_with_cur = give_list_with_days(datetime.now())
    await callback.message.edit_text(text='Выбери день для просмотра состояния оплаты:',
                                     reply_markup=show_next_seven_days_pay_kb(*next_seven_days_with_cur))


# Вываливаем список учеников в выбранный день, ❌ - не оплачено; ✅ - оплачено
# Чтобы поменять статус - надо нажать на время!
@router.callback_query(ShowDaysOfPayCallbackFactory.filter(), IsSomethingToConfirm())
async def process_show_status_student(callback: CallbackQuery, session: AsyncSession,
                                      callback_data: ShowDaysOfPayCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)

    list_lessons_not_formatted = await give_all_lessons_day_by_week_day(session,
                                                                        callback.from_user.id,
                                                                        week_date)
    intermediate_buttons = show_intermediate_information_lesson_day_status(list_lessons_not_formatted)
    await callback.message.edit_text(text='Нажмите, чтобы поменять статус:',
                                     reply_markup=await show_status_lesson_day_kb(intermediate_buttons,
                                                                                  session,
                                                                                  week_date_str))


# Ловим нажатие на кнопку и меняем статус оплаты: ❌ -> ✅ ; ✅ -> ❌
@router.callback_query(EditStatusPayCallbackFactory.filter())
async def process_edit_status_student(callback: CallbackQuery, session: AsyncSession,
                                      callback_data: EditStatusPayCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)
    # print(lesson_on, lesson_off)

    # Меняем статус в базе данных
    await change_status_pay_student(session,
                                    callback.from_user.id,
                                    week_date,
                                    lesson_on,
                                    lesson_off)

    list_lessons_not_formatted = await give_all_lessons_day_by_week_day(session,
                                                                        callback.from_user.id,
                                                                        week_date)

    intermediate_buttons = show_intermediate_information_lesson_day_status(list_lessons_not_formatted)

    await callback.message.edit_text(text='Нажмите, чтобы поменять статус:',
                                     reply_markup=await show_status_lesson_day_kb(intermediate_buttons,
                                                                                  session,
                                                                                  week_date_str))


# Случай, когда никто еще не выбрал занятие! И статус оплаты просто не появился!
@router.callback_query(ShowDaysOfPayCallbackFactory.filter(), ~IsSomethingToConfirm())
async def process_not_show_status_student(callback: CallbackQuery):
    await callback.answer("В данный момент никто не выбрал занятия!(")


########################################## кнопка МОЕ РАСПИСАНИЕ ######################################
@router.callback_query(F.data == 'schedule_show')
async def process_show_my_schedule(callback: CallbackQuery):
    next_seven_days_with_cur = give_list_with_days(datetime.now())
    await callback.message.edit_text(text='выберите день!)))))',
                                     reply_markup=show_next_seven_days_schedule_teacher_kb(
                                         *next_seven_days_with_cur)
                                     )


# Ловим апдейт с конкретным днем, и показываем все временные промежутки за день
@router.callback_query(ShowDaysOfScheduleTeacherCallbackFactory.filter(), IsSomethingToConfirm())
async def process_show_schedule_teacher(callback: CallbackQuery, session: AsyncSession,
                                        callback_data: ShowDaysOfScheduleTeacherCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)

    list_lessons_not_formatted = await give_all_lessons_day_by_week_day(session,
                                                                        callback.from_user.id,
                                                                        week_date)
    intermediate_buttons = show_intermediate_information_lesson_day_status(list_lessons_not_formatted)

    await callback.message.edit_text(text='Нажмите, чтобы посмотреть подробную информацию!:',
                                     reply_markup=show_schedule_lesson_day_kb(intermediate_buttons,
                                                                              session,
                                                                              week_date_str))


# Ловим апдейт и показываем информацию о конкретном промежутке
@router.callback_query(ShowInfoDayCallbackFactory.filter())
async def process_show_lesson_info(callback: CallbackQuery, session: AsyncSession,
                                   callback_data: ShowInfoDayCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)
    status = callback_data.status
    lesson_day = await give_information_of_one_lesson(session,
                                                      callback.from_user.id,
                                                      week_date,
                                                      lesson_on,
                                                      lesson_off)
    symbol = give_result_info(status)

    await callback.message.edit_text(text=f'Имя ученика: {lesson_day.student.name}\n'
                                          f'Фамилия: {lesson_day.student.surname}\n'
                                          f'...\n'
                                          f'{symbol}',
                                     reply_markup=back_to_show_or_delete_schedule_teacher
                                     (week_date_str,
                                      callback_data.lesson_on,
                                      callback_data.lesson_off)
                                     )


# Случай, когда нечего показывать в дне расписания
@router.callback_query(ShowDaysOfScheduleTeacherCallbackFactory.filter(), ~IsSomethingToConfirm())
async def process_show_schedule_teacher(callback: CallbackQuery):
    await callback.answer("Нечего показывать!")


################################ Нажали на кнопку __удалить__ в информации о дне ###################
@router.callback_query(DeleteDayScheduleCallbackFactory.filter())
async def process_delete_lesson(callback: CallbackQuery, session: AsyncSession,
                                callback_data: DeleteDayScheduleCallbackFactory):
    week_date = give_date_format_fsm(callback_data.week_date)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)
    await delete_lesson(session,
                        week_date,
                        lesson_on,
                        lesson_off)

    await callback.message.edit_text(text='Удаление произошло успешно!',
                                     reply_markup=back_to_show_schedule_teacher(callback_data.week_date))
