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

from callback_factory.student import ExistFieldCallbackFactory, EmptyAddFieldCallbackFactory, \
    DeleteFieldCallbackFactory, EmptyRemoveFieldCallbackFactory, ShowDaysOfScheduleCallbackFactory, \
    StartEndLessonDayCallbackFactory, PlugPenaltyStudentCallbackFactory
from database.student_requirements import command_get_all_teachers, command_add_students, give_lessons_week_for_day, \
    add_lesson_day, give_teacher_id_by_student_id, give_all_busy_time_intervals, \
    give_all_lessons_for_day, remove_lesson_day, give_week_id_by_teacher_id, give_all_information_teacher, \
    give_information_of_lesson, delete_student_profile, give_students_penalty
from filters.student_filters import IsStudentInDatabase, IsInputFieldAlpha, IsInputFieldDigit, \
    FindNextSevenDaysFromKeyboard, IsMoveRightAddMenu, IsMoveLeftMenu, IsTeacherDidSlots, IsStudentChooseSlots, \
    IsMoveRightRemoveMenu, IsLessonsInChoseDay, IsTimeNotExpired, IsFreeSlots, IsTeacherDidSystemPenalties, IsStudentHasPenalties
from keyboards.everyone_kb import create_start_kb
from keyboards.student_kb import create_entrance_kb, create_teachers_choice_kb, create_level_choice_kb, \
    create_back_to_entrance_kb, create_authorization_kb, show_next_seven_days_settings_kb, create_menu_add_remove_kb, \
    create_choose_time_student_kb, create_delete_lessons_menu, show_next_seven_days_schedule_kb, all_lessons_for_day_kb, \
    create_button_for_back_to_all_lessons_day, create_settings_profile_kb, create_information_penalties
from services.services import give_list_with_days, create_choose_time_student, give_date_format_fsm, \
    give_time_format_fsm, create_delete_time_student, show_all_lessons_for_day, give_result_status_timeinterval, \
    give_result_info

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
                                     reply_markup=show_next_seven_days_settings_kb(*next_seven_days_with_cur))

    await state.clear()


############################ Здесь выбираем добавить/удалить окошко ###################################3
@router.callback_query(FindNextSevenDaysFromKeyboard(), StateFilter(default_state))
async def process_menu_add_remove(callback: CallbackQuery, state: FSMContext):
    await state.update_data(page=1,
                            week_date=callback.data)

    await callback.message.edit_text(text='Выберите что вы хотите сделать с уроками'
                                     ,
                                     reply_markup=create_menu_add_remove_kb())


###################################### Кнопка ДОБАВИТЬ ########################################3
# Нажимаем добавить, открываем меню со свободными слотами
@router.callback_query(F.data == 'add_gap_student', IsTeacherDidSlots(), IsFreeSlots())
async def process_add_time_study(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page']

    student = await give_teacher_id_by_student_id(session,
                                                  callback.from_user.id)

    lessons_busy = await give_all_busy_time_intervals(session,
                                                      student.teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date)

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

    student = await give_teacher_id_by_student_id(session,
                                                  callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      student.teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date)

    await callback.message.edit_text(text='Выбери слот старта занятия!\n'
                                          'Все слоты по 30 минут!\n'
                                     ,
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page
                                     ))


# Движемся влево в нашем меню занятий
@router.callback_query(F.data == 'move_left_add', IsMoveLeftMenu())
async def process_move_right_add_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page'] - 1
    await state.update_data(page=page)

    student = await give_teacher_id_by_student_id(session,
                                                  callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      student.teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date)

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
@router.callback_query(F.data == 'move_left_add', ~IsMoveLeftMenu())
async def process_not_move_right_add_menu(callback: CallbackQuery):
    await callback.answer('Двигаться некуда!')


# Нажимаем на занятие и оно появляется в нашей базе данных!
@router.callback_query(ExistFieldCallbackFactory.filter())
async def process_touch_menu_add(callback: CallbackQuery, session: AsyncSession, state: FSMContext,
                                 callback_data: ExistFieldCallbackFactory):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)

    student = await give_teacher_id_by_student_id(session,
                                                  callback.from_user.id)
    lesson_start = give_time_format_fsm(callback_data.lesson_start)
    lesson_finished = give_time_format_fsm(callback_data.lesson_finished)

    week_id = await give_week_id_by_teacher_id(session,
                                               student.teacher_id,
                                               week_date,
                                               lesson_start,
                                               lesson_finished)
    await add_lesson_day(session=session,
                         week_date=week_date,
                         week_id=week_id,
                         teacher_id=student.teacher_id,
                         student_id=callback.from_user.id,
                         lesson_start=lesson_start,
                         lesson_finished=lesson_finished,
                         )

    student = await give_teacher_id_by_student_id(session,
                                                  callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      student.teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date)
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


# Случай, когда свободных занятий больше нет!
@router.callback_query(F.data == 'add_gap_student', ~IsFreeSlots())
async def process_not_add_time_study(callback: CallbackQuery):
    await callback.answer("Свободных мест больше нет!")


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


# Настраиваем удаление записей по нажатию на кнопку! + Ограничение по удалению не наступило!
@router.callback_query(DeleteFieldCallbackFactory.filter(), IsTimeNotExpired())
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


# Движение влево в меню удаления
@router.callback_query(F.data == 'move_left_remove', IsMoveLeftMenu())
async def process_move_right_remove(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page'] - 1
    await state.update_data(page=page)

    all_busy_lessons = await give_all_lessons_for_day(session,
                                                      week_date,
                                                      callback.from_user.id)
    dict_for_6_lessons = create_delete_time_student(all_busy_lessons)
    await callback.message.edit_text(text='Нажмите, чтобы удалить запись!',
                                     reply_markup=create_delete_lessons_menu(dict_for_6_lessons,
                                                                             week_date_str,
                                                                             page))


# Движение вправо в меню удаления
@router.callback_query(F.data == 'move_right_remove', IsMoveRightRemoveMenu())
async def process_move_left_remove(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page'] + 1
    await state.update_data(page=page)

    all_busy_lessons = await give_all_lessons_for_day(session,
                                                      week_date,
                                                      callback.from_user.id)
    dict_for_6_lessons = create_delete_time_student(all_busy_lessons)
    await callback.message.edit_text(text='Нажмите, чтобы удалить запись!',
                                     reply_markup=create_delete_lessons_menu(dict_for_6_lessons,
                                                                             week_date_str,
                                                                             page))


# Случай, при нажатии на кнопку __удалить__ нечего удалять
@router.callback_query(F.data == 'remove_gap_student', ~IsStudentChooseSlots())
async def process_not_remove_time_study(callback: CallbackQuery):
    await callback.answer(text='Нечего удалять!')


# Случай, когда мы не можем удалить, потому что время отмены истекло!
@router.callback_query(DeleteFieldCallbackFactory.filter(), ~IsTimeNotExpired())
async def process_not_touch_menu_remove(callback: CallbackQuery):
    await callback.answer(text='Время удаления истекло!')


# Случай, когда нажимаем на пустую кнопку
@router.callback_query(EmptyRemoveFieldCallbackFactory.filter())
async def process_touch_empty_button(callback: CallbackQuery):
    await callback.answer()


# Случай, когда влево двигаться некуда!
@router.callback_query(F.data == 'move_left_remove', ~IsMoveLeftMenu())
async def process_not_move_right_remove(callback: CallbackQuery):
    await callback.answer(text='Двигаться некуда!')


# Случай, когда двигаться вправо некуда!
@router.callback_query(F.data == 'move_right_remove', ~IsMoveRightRemoveMenu())
async def process_not_move_left_remove(callback: CallbackQuery):
    await callback.answer(text='Двигаться некуда!')


########################## Кнопка __Мое расписание__ ######################################
# Нажимаем на кнопку Мое расписание и вываливается список доступных дней
@router.callback_query(F.data == 'show_schedule')
async def process_show_schedule(callback: CallbackQuery, state: FSMContext):
    next_seven_days_with_cur = give_list_with_days(datetime.now())
    # print(next_seven_days_with_cur)

    await callback.message.edit_text(text='Выберите дату вашего расписания!',
                                     reply_markup=show_next_seven_days_schedule_kb(*next_seven_days_with_cur))
    await state.clear()


# Выбираем день занятия (нажимаем на этот день)
@router.callback_query(ShowDaysOfScheduleCallbackFactory.filter(), IsLessonsInChoseDay())
async def process_show_lessons_for_day(callback: CallbackQuery, session: AsyncSession,
                                       callback_data: ShowDaysOfScheduleCallbackFactory,
                                       state: FSMContext):
    week_date = give_date_format_fsm(callback_data.week_date)
    await state.update_data(week_date=callback_data.week_date)

    all_lessons_for_day_not_ordered = await give_all_lessons_for_day(session,
                                                                     week_date,
                                                                     callback.from_user.id)
    all_lessons_for_day_ordered_list = show_all_lessons_for_day(all_lessons_for_day_not_ordered)

    await callback.message.edit_text(text='Чтобы посмотреть подробности нажмии на занятие!',
                                     reply_markup=all_lessons_for_day_kb(all_lessons_for_day_ordered_list)
                                     )


@router.callback_query(ShowDaysOfScheduleCallbackFactory.filter(), ~IsLessonsInChoseDay())
async def process_not_show_lessons_for_day(callback: CallbackQuery):
    await callback.answer('В данный момент нет выбранных занятий!')


# Нажимаем на временной промежуток, чтобы посмотреть подробную информацию
@router.callback_query(StartEndLessonDayCallbackFactory.filter())
async def process_show_full_information_lesson(callback: CallbackQuery, session: AsyncSession,
                                               callback_data: StartEndLessonDayCallbackFactory,
                                               state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    student = await give_teacher_id_by_student_id(session,
                                                  callback.from_user.id)

    teacher = await give_all_information_teacher(session,
                                                 student.teacher_id)
    # Проверка на оплату
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)
    information_of_status_lesson = await give_information_of_lesson(session,
                                                                    callback.from_user.id,
                                                                    week_date,
                                                                    lesson_on,
                                                                    lesson_off)

    result_status, counter_lessons = give_result_status_timeinterval(information_of_status_lesson)
    status_info = give_result_info(result_status)

    # Выводим информацию
    await callback.message.edit_text(text=f'Ваш преподаватель: {teacher.surname} {teacher.name}\n'
                                          f'Время занятия: {callback_data.lesson_on} -'
                                          f' {callback_data.lesson_off}\n'
                                          f'Стоимость занятия: {student.price * counter_lessons / 2} рублей\n'
                                          f'Просьба оформлять перевод в формате:\n '
                                          f'Имя-Предмет-Время_начала-Время_окончания-сумма\n'
                                          f'Статус оплаты: {status_info}',
                                     reply_markup=create_button_for_back_to_all_lessons_day(week_date_str)
                                     )


###################################### Кнопка НАСТРОЙКИ #############################################

@router.callback_query(F.data == 'settings_student')
async def process_create_menu_settings(callback: CallbackQuery):
    await callback.message.edit_text(text='Выберите, что хотите сделать!',
                                     reply_markup=create_settings_profile_kb())


# Выбрали __Редактировать профиль__
@router.callback_query(F.data == 'edit_profile', StateFilter(default_state))
async def process_change_settings_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите ваше имя!')

    await state.set_state(FSMRegistrationStudentForm.fill_name)


@router.callback_query(F.data == 'delete_profile')
async def process_delete_profile(callback: CallbackQuery, session: AsyncSession):
    await delete_student_profile(session,
                                 callback.from_user.id)
    await callback.message.edit_text(text="Здравствуйте, выберите роль!",
                                     reply_markup=create_start_kb())


######################################## Кнопка ШТРАФЫ #############################################
@router.callback_query(F.data == 'penalties', IsTeacherDidSystemPenalties(), IsStudentHasPenalties())
async def process_penalties(callback: CallbackQuery, session: AsyncSession):
    students_penalty = await give_students_penalty(session, callback.from_user.id)

    await callback.message.edit_text(text='Ваши пенальти!',
                                     reply_markup=create_information_penalties(students_penalty))


# Нажатие на кнопки с информацией - ничего не должно происходить
@router.callback_query(PlugPenaltyStudentCallbackFactory.filter())
async def process_not_penalties(callback: CallbackQuery):
    await callback.answer()


# Случай, когда учитель не установил систему пенальти!
@router.callback_query(F.data == 'penalties', ~IsTeacherDidSystemPenalties())
async def process_not_work_penalties(callback: CallbackQuery):
    await callback.answer('Ваш репетитор отключил систему пенальти!')


# Случай, когда у ученика нет пенальти!
@router.callback_query(F.data == 'penalties', ~IsStudentHasPenalties())
async def process_not_penalties(callback: CallbackQuery):
    await callback.answer('У вас нет пенальти!')
