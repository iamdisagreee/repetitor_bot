from datetime import date, datetime, timedelta, time
from pprint import pprint

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm import state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from callback_factory.student import ExistFieldCallbackFactory, EmptyAddFieldCallbackFactory, DeleteFieldCallbackFactory
from database.student_requirements import command_get_all_teachers, command_add_students, give_lessons_week_for_day, \
    add_lesson_day, give_teacher_id_by_student_id, give_all_busy_time_intervals, \
    give_all_lessons_for_day, remove_lesson_day, give_week_id_by_teacher_id
from filters.student_filters import IsStudentInDatabase, IsInputFieldAlpha, IsInputFieldDigit, \
    FindNextSevenDaysFromKeyboard, IsMoveRightAddMenu, IsMoveLeftAddMenu, IsTeacherDidSlots, IsStudentChooseSlots
from keyboards.student_kb import create_entrance_kb, create_teachers_choice_kb, create_level_choice_kb, \
    create_back_to_entrance_kb, create_authorization_kb, show_next_seven_days_kb, create_menu_add_remove_kb, \
    create_choose_time_student_kb, create_delete_lessons_menu
from services.services import give_list_with_days, create_choose_time_student, give_date_format_fsm, \
    give_time_format_fsm, create_delete_time_student

router = Router()


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


############################### Логика входа в меню идентификации #######################################

@router.callback_query(F.data == 'student_entrance')
async def process_entrance(callback: CallbackQuery):
    await callback.message.edit_text(text='Это меню идентификации!\n'
                                          'Выбери, что хочешь сделать',
                                     reply_markup=create_entrance_kb())


################################ Логика регистрации студента ############################################

# Кнопка __регистрация__
@router.callback_query(F.data == 'reg_student', ~IsStudentInDatabase())
async def process_start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите ваше имя!')

    await state.set_state(FSMRegistrationStudentForm.fill_name)


# Вводим имя и просим ввести фамилию
@router.message(StateFilter(FSMRegistrationStudentForm.fill_name), IsInputFieldAlpha())
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите фамилию!')
    await state.set_state(FSMRegistrationStudentForm.fill_surname)


# Вводим фамилию и просим ввести город
@router.message(StateFilter(FSMRegistrationStudentForm.fill_surname), IsInputFieldAlpha())
async def process_surname_sent(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите город проживания!')
    await state.set_state(FSMRegistrationStudentForm.fill_city)


# Вводим город и проосим ввести место обучения
@router.message(StateFilter(FSMRegistrationStudentForm.fill_city), IsInputFieldAlpha())
async def process_city_sent(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(text='Спасибо!\n\nА теперь введите место обучения!')
    await state.set_state(FSMRegistrationStudentForm.fill_place_study)


# Вводим место обучения и просим выбрать курс/класс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_place_study), IsInputFieldAlpha())
async def process_city_sent(message: Message, session: AsyncSession, state: FSMContext):
    await state.update_data(place_study=message.text)
    await message.answer(text='Спасибо! А теперь Выберите, что заполнить:\n'
                              'Курс или класс обучения',
                         reply_markup=create_level_choice_kb())

    await state.set_state(FSMRegistrationStudentForm.fill_level)


# Меняем значение состояние, чтобы ввести класс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level), F.text == 'Класс обучения')
async def process_change_state_class(message: Message, state: FSMContext):
    await message.answer(text='Введите класс:')
    await state.set_state(FSMRegistrationStudentForm.fill_level_class)


# Вводим клас обучения
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_class), IsInputFieldDigit())
async def process_class_sent(message: Message, state: FSMContext):
    await state.update_data(class_learning=message.text)
    await state.set_state(FSMRegistrationStudentForm.fill_subject)
    await message.answer(text='Введите предмет:')


# Меняем значение состояние, чтобы ввести курс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level), F.text == 'Курс обучения')
async def process_change_state_course(message: Message, state: FSMContext):
    await message.answer(text='Введите курс:')
    await state.set_state(FSMRegistrationStudentForm.fill_level_course)


# Вводим курс обучения
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_course), IsInputFieldDigit())
async def process_class_sent(message: Message, state: FSMContext):
    await state.update_data(course_learning=message.text)
    await state.set_state(FSMRegistrationStudentForm.fill_subject)
    await message.answer(text='Введите предмет:')


# Вводим предмет и просим выбрать учителя!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_subject), IsInputFieldAlpha())
async def process_subject_sent(message: Message, session: AsyncSession, state: FSMContext):
    await state.update_data(subject=message.text)

    all_teachers = await command_get_all_teachers(session)
    await message.answer(text='Отлично! А теперь выберите учителя!',
                         reply_markup=create_teachers_choice_kb(all_teachers))
    await state.set_state(FSMRegistrationStudentForm.fill_teacher)


# Выбрали учителя и просим указать стоимость занятий
@router.callback_query(StateFilter(FSMRegistrationStudentForm.fill_teacher))
async def process_teacher_sent(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(teacher_id=callback.data)
    await callback.message.answer(text='Отлично! А теперь введи стоимость'
                                       'занятий за час!')
    await state.set_state(FSMRegistrationStudentForm.fill_price)


# Указали стоимость -> отправляем данные на сервер о студенте
@router.message(StateFilter(FSMRegistrationStudentForm.fill_price), IsInputFieldDigit())
async def process_price_sent(message: Message, session: AsyncSession, state: FSMContext):
    await state.update_data(price=message.text)

    student_form = await state.get_data()
    await command_add_students(session,
                               message.from_user.id,
                               **student_form)

    await state.clear()

    await message.answer(text="Спасибо, что ввели данные!\n\n"
                              "Нажми на кнопку, чтобы вернуться!!!",
                         reply_markup=create_back_to_entrance_kb())


# Случай, когда ученик находится в бд, но хочет зарегестрироваться
@router.callback_query(F.data == 'reg_student', IsStudentInDatabase())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Вы уже зарегестрированы!")


# Случай, когда еще не зарегестрировался, но хочет зайти авторизоваться
@router.callback_query(F.data == 'auth_student', ~IsStudentInDatabase())
async def process_not_start_authentication(callback: CallbackQuery):
    await callback.answer("Вы еще не зарегестрированы!")


# Случай, когда имя неправильное!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_name), ~IsInputFieldAlpha())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на текст\n"
                          "Попробуй заново!!")


# Случай, когда фамилия неправильная!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_surname), ~IsInputFieldAlpha())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на текст\n"
                          "Попробуй заново!!")


# Случай, когда город неправильная!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_city), ~IsInputFieldAlpha())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на текст\n"
                          "Попробуй заново!!")


# Случай, когда место обучения неправильное!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_place_study), ~IsInputFieldAlpha())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на текст\n"
                          "Попробуй заново!!")


# Случай, когда класс неправильный!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_class), ~IsInputFieldDigit())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на число\n"
                          "Попробуй заново!!")


# Случай, когда класс неправильный!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_course), ~IsInputFieldDigit())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на число\n"
                          "Попробуй заново!!")


# Случай, когда цена неправильная!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_price), ~IsInputFieldDigit())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer("Это не похоже на число\n"
                          "Попробуй заново!!")


######################## МЕНЮ ПОЛЬЗОВАТЕЛЯ - АВТОРИЗАЦИЯ ################################
@router.callback_query(F.data == 'auth_student')
async def process_start_authorization(callback: CallbackQuery):
    await callback.message.edit_text(text='Добро пожаловать в главное меню!',
                                     reply_markup=create_authorization_kb())


###################### Логика настройки меню пользователя (добавление/удаление) #########
@router.callback_query(F.data == 'settings_schedule')
async def process_settings_schedule(callback: CallbackQuery, state: FSMContext):
    next_seven_days_with_cur = give_list_with_days(datetime.now())

    await callback.message.edit_text(text='Выберите дату, чтобы выбрать время!',
                                     reply_markup=show_next_seven_days_kb(*next_seven_days_with_cur))

    await state.clear()


############################ Здесь выбираем добавить/удалить окошко ###################################3
@router.callback_query(FindNextSevenDaysFromKeyboard(), StateFilter(default_state))
async def process_menu_add_remove(callback: CallbackQuery, state: FSMContext):
    await state.update_data(page=1,
                            week_date=callback.data)

    await callback.message.edit_text(text='Выберите что вы хотите сделать с уроками'
                                     ,
                                     reply_markup=create_menu_add_remove_kb())


###################################### Кнопка добавить ########################################3
# Нажимаем добавить, открываем меню со свободными слотами
@router.callback_query(F.data == 'add_gap_student', IsTeacherDidSlots())
async def process_add_time_study(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page']

    teacher_id = await give_teacher_id_by_student_id(session,
                                                     callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy)

    await callback.message.edit_text(text='Выбери слот старта занятия!\n'
                                          'Все слоты по 30 минут!\n'
                                          'Если свободных слотов НЕТ - это значит, что все разобрано!!!!',
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page
                                     ))


# Движемся вправо в нашем меню занятий
@router.callback_query(F.data == 'move_right_add', IsMoveRightAddMenu())
async def process_move_right_add_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page'] + 1
    await state.update_data(page=page)

    teacher_id = await give_teacher_id_by_student_id(session,
                                                     callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy)

    await callback.message.edit_text(text='Выбери слот старта занятия!\n'
                                          'Все слоты по 30 минут!\n'
                                     ,
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page
                                     ))


# Движемся влево в нашем меню занятий
@router.callback_query(F.data == 'move_left_add', IsMoveLeftAddMenu())
async def process_move_right_add_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page'] - 1
    await state.update_data(page=page)

    teacher_id = await give_teacher_id_by_student_id(session,
                                                     callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy)

    await callback.message.edit_text(text='Выбери слот старта занятия!\n'
                                          'Все слоты по 30 минут!',
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page
                                     ))


# Случай, когда вправо больше нельзя двигаться
@router.callback_query(F.data == 'move_right_add', ~IsMoveRightAddMenu())
async def process_not_move_right_add_menu(callback: CallbackQuery):
    await callback.answer('Двигаться некуда!')


# Случай, когда влево нельзя двигаться
@router.callback_query(F.data == 'move_left_add', ~IsMoveLeftAddMenu())
async def process_not_move_right_add_menu(callback: CallbackQuery):
    await callback.answer('Двигаться некуда!')


# Нажимаем на занятие и оно появляется в нашей базе данных!
@router.callback_query(ExistFieldCallbackFactory.filter())
async def process_touch_menu_add(callback: CallbackQuery, session: AsyncSession, state: FSMContext,
                                 callback_data: ExistFieldCallbackFactory):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)

    teacher_id = await give_teacher_id_by_student_id(session,
                                                     callback.from_user.id)
    lesson_start = give_time_format_fsm(callback_data.lesson_start)
    lesson_finished = give_time_format_fsm(callback_data.lesson_finished)

    week_id = await give_week_id_by_teacher_id(session,
                                                  teacher_id,
                                                  week_date,
                                                  lesson_start,
                                                  lesson_finished)
    await add_lesson_day(session=session,
                         week_date=week_date,
                         week_id=week_id,
                         teacher_id=teacher_id,
                         student_id=callback.from_user.id,
                         lesson_start=lesson_start,
                         lesson_finished=lesson_finished,
                         )

    teacher_id = await give_teacher_id_by_student_id(session,
                                                     callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy)
    page = state_dict['page']
    await callback.message.edit_text(text='Выбери слот старта занятия!\n'
                                          'Все слоты по 30 минут!',
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page
                                     ))


# Нажимаем на пустую кнопку
@router.callback_query(EmptyAddFieldCallbackFactory.filter())
async def process_touch_empty_button(callback: CallbackQuery):
    await callback.answer()


# Случай, когда учитель еще не выставил слоты!
@router.callback_query(F.data == 'add_gap_student', ~IsTeacherDidSlots())
async def process_teacher_did_not_slots(callback: CallbackQuery):
    await callback.answer("Репетитор еще не выставил слоты!")


###################################### Кнопка удалить ###########################################

@router.callback_query(F.data == 'remove_gap_student', IsStudentChooseSlots())
async def process_remove_time_study(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page']

    all_busy_lessons = await give_all_lessons_for_day(session,
                                                      week_date,
                                                      callback.from_user.id)
    dict_for_6_lessons = create_delete_time_student(all_busy_lessons)
    await callback.message.edit_text(text='Нажмите, чтобы удалить запись!',
                                     reply_markup=create_delete_lessons_menu(dict_for_6_lessons,
                                                                             week_date_str,
                                                                             page))


# Настраиваем удаление записей по нажатию на кнопку!
@router.callback_query(DeleteFieldCallbackFactory.filter())
async def process_touch_menu_remove(callback: CallbackQuery, session: AsyncSession, state: FSMContext,
                                    callback_data: DeleteFieldCallbackFactory):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page']

    lesson_start = give_time_format_fsm(callback_data.lesson_start)
    lesson_finished = give_time_format_fsm(callback_data.lesson_finished)

    await remove_lesson_day(session,
                            callback.from_user.id,
                            week_date,
                            lesson_start,
                            lesson_finished
                            )

    all_busy_lessons = await give_all_lessons_for_day(session,
                                                      week_date,
                                                      callback.from_user.id)
    dict_for_6_lessons = create_delete_time_student(all_busy_lessons)
    await callback.message.edit_text(text='Нажмите, чтобы удалить запись!',
                                     reply_markup=create_delete_lessons_menu(dict_for_6_lessons,
                                                                             week_date_str,
                                                                             page)
                                     )
