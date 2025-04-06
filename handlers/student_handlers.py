import time
from datetime import datetime, date, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter

from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq_nats import NATSKeyValueScheduleSource
from sqlalchemy import select

from callback_factory.student_factories import ExistFieldCallbackFactory, EmptyAddFieldCallbackFactory, \
    DeleteFieldCallbackFactory, EmptyRemoveFieldCallbackFactory, ShowDaysOfScheduleCallbackFactory, \
    StartEndLessonDayCallbackFactory, PlugPenaltyStudentCallbackFactory, InformationLessonCallbackFactory, \
    RemoveDayOfScheduleCallbackFactory
from callback_factory.taskiq_factories import InformationLessonWithDeleteCallbackFactory
from database import Student, LessonDay
from database.student_requests import command_get_all_teachers, command_add_students, give_lessons_week_for_day, \
    add_lesson_day, give_teacher_by_student_id, give_all_busy_time_intervals, \
    give_all_lessons_for_day, remove_lesson_day, give_week_id_by_teacher_id, \
    give_information_of_lesson, delete_student_profile, give_students_penalty, give_all_information_teacher, \
    delete_gap_lessons_by_student, give_all_debts_student
from filters.student_filters import IsStudentInDatabase, IsInputFieldAlpha, \
    FindNextSevenDaysFromKeyboard, IsMoveRightAddMenu, IsMoveLeftMenu, IsTeacherDidSlots, IsStudentChooseSlots, \
    IsMoveRightRemoveMenu, IsLessonsInChoseDay, IsTimeNotExpired, IsFreeSlots, IsTeacherDidSystemPenalties, \
    IsStudentHasPenalties, StudentStartFilter, IsRightClassCourse, IsRightPrice, \
    IsNotAlreadyConfirmed, IsUntilTimeNotification, IsDebtsStudent
from fsm.fsm_student import FSMRegistrationStudentForm
from keyboards.everyone_kb import create_start_kb
from keyboards.student_kb import create_entrance_kb, create_teachers_choice_kb, create_level_choice_kb, \
    create_back_to_entrance_kb, create_authorization_kb, show_next_seven_days_settings_kb, create_menu_add_remove_kb, \
    create_choose_time_student_kb, create_delete_lessons_menu, show_next_seven_days_schedule_kb, all_lessons_for_day_kb, \
    create_button_for_back_to_all_lessons_day, create_settings_profile_kb, create_information_penalties, \
    create_back_to_settings_student_kb, create_confirm_payment_teacher_kb, \
    create_ok_remove_day_schedule_student_kb, create_debts_student_kb
from lexicon.lexicon_all import LEXICON_ALL
from lexicon.lexicon_student import LEXICON_STUDENT
from services.services import give_list_with_days, create_choose_time_student, give_date_format_fsm, \
    give_time_format_fsm, create_delete_time_student, show_all_lessons_for_day, \
    give_text_information_lesson, course_class_choose, COUNT_BAN, give_result_status_timeinterval, NUMERIC_DATE, \
    create_list_gaps_by_time_on_and_off, is_correct_sent_delete_lesson_for_teacher
from tasks import notice_lesson_certain_time_student

# Преподаватель - нет доступа
# Ученик - открываем
router = Router()
router.callback_query.filter(StudentStartFilter())


############################### Логика входа в меню идентификации #######################################

@router.callback_query(F.data == 'student_entrance')
async def process_entrance(callback: CallbackQuery):
    # await notice_lesson_certain_time_student.kiq(callback.from_user.id)
    await callback.message.edit_text(text=LEXICON_STUDENT['menu_identification'],
                                     reply_markup=create_entrance_kb())


################################ Логика регистрации студента ############################################

# Кнопка __регистрация__
@router.callback_query(F.data == 'reg_student', ~IsStudentInDatabase())
async def process_start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON_STUDENT['fill_name'])

    await state.set_state(FSMRegistrationStudentForm.fill_name)


# Ловим имя и просим ввести фамилию
@router.message(StateFilter(FSMRegistrationStudentForm.fill_name), IsInputFieldAlpha())
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text.capitalize())
    await message.answer(text=LEXICON_STUDENT['fill_surname'])
    await state.set_state(FSMRegistrationStudentForm.fill_surname)


# Ловим фамилию и просим ввести город
@router.message(StateFilter(FSMRegistrationStudentForm.fill_surname), IsInputFieldAlpha())
async def process_surname_sent(message: Message, state: FSMContext):
    await state.update_data(surname=message.text.capitalize())
    await message.answer(text=LEXICON_STUDENT['fill_city'])
    await state.set_state(FSMRegistrationStudentForm.fill_city)


# Ловим город и просим ввести место обучения
@router.message(StateFilter(FSMRegistrationStudentForm.fill_city), IsInputFieldAlpha())
async def process_city_sent(message: Message, state: FSMContext):
    await state.update_data(city=message.text.capitalize())
    await message.answer(text=LEXICON_STUDENT['fill_place_study'])
    await state.set_state(FSMRegistrationStudentForm.fill_place_study)


# Ловим место обучения и просим выбрать курс/класс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_place_study))
async def process_city_sent(message: Message, state: FSMContext):
    await state.update_data(place_study=message.text)
    await message.answer(text=LEXICON_STUDENT['fill_level_choice'],
                         reply_markup=create_level_choice_kb())

    await state.set_state(FSMRegistrationStudentForm.fill_level)


# Меняем значение состояние, чтобы ввести класс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level),
                F.text == LEXICON_STUDENT['class_learning'])
async def process_change_state_class(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_STUDENT['fill_class'],
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMRegistrationStudentForm.fill_level_class)


# Ловим класс обучения, предлагаем ввести предмет
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_class), IsRightClassCourse())
async def process_class_sent(message: Message, state: FSMContext):
    await state.update_data(class_learning=message.text)
    await state.set_state(FSMRegistrationStudentForm.fill_subject)
    await message.answer(text=LEXICON_STUDENT['fill_subject'])


# Меняем значение состояние, чтобы ввести курс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level),
                F.text == LEXICON_STUDENT['course_learning'])
async def process_change_state_course(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_STUDENT['fill_course'],
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMRegistrationStudentForm.fill_level_course)


# Ловим курс обучения, предлагаем ввести предмет
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_course), IsRightClassCourse())
async def process_class_sent(message: Message, state: FSMContext):
    await state.update_data(course_learning=message.text)
    await state.set_state(FSMRegistrationStudentForm.fill_subject)
    await message.answer(text=LEXICON_STUDENT['fill_subject'])


# Ловим предмет и просим выбрать учителя!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_subject), IsInputFieldAlpha())
async def process_subject_sent(message: Message, session: AsyncSession, state: FSMContext):
    await state.update_data(subject=message.text.capitalize())

    all_teachers = await command_get_all_teachers(session)
    await message.answer(text=LEXICON_STUDENT['fill_teacher'],
                         reply_markup=create_teachers_choice_kb(all_teachers))
    await state.set_state(FSMRegistrationStudentForm.fill_teacher)


# Выбрали учителя и просим указать стоимость занятий
@router.callback_query(StateFilter(FSMRegistrationStudentForm.fill_teacher))
async def process_teacher_sent(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(teacher_id=callback.data)
    await callback.message.answer(text=LEXICON_STUDENT['fill_price'])
    await state.set_state(FSMRegistrationStudentForm.fill_price)


# Поймали стоимость -> просим ввести время, за которое будет приходить уведомление о занятии (ЧАСЫ:МИНУТЫ)
@router.message(StateFilter(FSMRegistrationStudentForm.fill_price), IsRightPrice())
async def process_price_sent(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer(text=LEXICON_STUDENT['fill_until_time_notification'])
    await state.set_state(FSMRegistrationStudentForm.fill_until_time_notification)

# Поймали время, за которое будет приходить уведомление о занятии ->
# передаем данные, чистим состояние
@router.message(StateFilter(FSMRegistrationStudentForm.fill_until_time_notification), IsUntilTimeNotification())
async def process_until_time_notification_sent(message: Message, session: AsyncSession, state: FSMContext):
    await state.update_data(until_time_notification=message.text)
    student_form = await state.get_data()
    await command_add_students(session,
                                message.from_user.id,
                                **student_form)
    await state.clear()

    await message.answer(text=LEXICON_STUDENT['access_registration_profile'],
                             reply_markup=create_back_to_entrance_kb())

###Неправильные фильтры для анкеты
# Имя неправильного формата!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_name), ~IsInputFieldAlpha())
async def process_name_not_sent(message: Message):
    await message.answer(text=LEXICON_STUDENT['not_fill_name'])


# Фамилия неправильного формата!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_surname), ~IsInputFieldAlpha())
async def process_surname_not_sent(message: Message):
    await message.answer(text=LEXICON_STUDENT['not_fill_surname'])


# Город неправильного формата!
@router.message(StateFilter(FSMRegistrationStudentForm.fill_city), ~IsInputFieldAlpha())
async def process_city_sent(message: Message):
    await message.answer(LEXICON_STUDENT['not_fill_city'])


# Случай, когда написали текст, вместо выбора класс/курс
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level),
                ~F.text.in_([LEXICON_STUDENT['course_learning'],
                             LEXICON_STUDENT['class_learning']]))
async def process_wrong_level_choice(message: Message):
    await message.answer(text=LEXICON_STUDENT['not_fill_level_choice'],
                         reply_markup=create_level_choice_kb())


# Некорректный ввод класса
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_class), ~IsRightClassCourse())
async def process_class_sent(message: Message):
    await message.answer(text=LEXICON_STUDENT['not_fill_class'])


# Случай, когда курс ввели неправильно
@router.message(StateFilter(FSMRegistrationStudentForm.fill_level_course), ~IsRightClassCourse())
async def process_class_sent(message: Message):
    await message.answer(LEXICON_STUDENT['not_fill_course'])


# Случай, когда неправильно ввели предмет
@router.message(StateFilter(FSMRegistrationStudentForm.fill_subject), ~IsInputFieldAlpha())
async def process_subject_sent(message: Message):
    await message.answer(text=LEXICON_STUDENT['not_fill_subject'])


# Стоимость указана неправильно
@router.message(StateFilter(FSMRegistrationStudentForm.fill_price), ~IsRightPrice())
async def process_price_sent(message: Message):
    await message.answer(LEXICON_STUDENT['not_fill_price'])

# Неправильное время, за которое будет приходить уведомление о занятии
@router.message(StateFilter(FSMRegistrationStudentForm.fill_until_time_notification))
async def process_not_until_time_notification(message: Message):
    await message.answer(LEXICON_STUDENT['not_fill_until_time_notification'])

# Случай, когда ученик находится в бд, но хочет зарегистрироваться
@router.callback_query(F.data == 'reg_student', IsStudentInDatabase())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['now_registered'], show_alert=True)


# Случай, когда еще не зарегистрировался, но хочет зайти авторизоваться
@router.callback_query(F.data == 'auth_student', ~IsStudentInDatabase())
async def process_not_start_authentication(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['not_registered'])


######################## МЕНЮ ПОЛЬЗОВАТЕЛЯ - АВТОРИЗАЦИЯ ################################
@router.callback_query(F.data == 'auth_student')
async def process_start_authorization(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON_STUDENT['main_menu_authorization'],
                                     reply_markup=create_authorization_kb())


###################### Логика настройки расписания (добавление/удаление) #########
@router.callback_query(F.data == 'settings_schedule')
async def process_settings_schedule(callback: CallbackQuery, state: FSMContext):
    next_seven_days_with_cur = give_list_with_days(datetime.now())

    await callback.message.edit_text(text=LEXICON_STUDENT['schedule_student_menu'],
                                     reply_markup=show_next_seven_days_settings_kb(*next_seven_days_with_cur))
    await state.clear()


############################ Здесь выбираем добавить/удалить окошко ###################################3
@router.callback_query(FindNextSevenDaysFromKeyboard())
async def process_menu_add_remove(callback: CallbackQuery, state: FSMContext):
    await state.update_data(page=1,
                            week_date=callback.data)

    await callback.message.edit_text(text=LEXICON_STUDENT['schedule_changes_add_remove'],
                                     reply_markup=create_menu_add_remove_kb())


###################################### Кнопка ВЫБРАТЬ ########################################3
# Нажимаем добавить, открываем меню со свободными слотами
@router.callback_query(F.data == 'add_gap_student', IsTeacherDidSlots(), IsFreeSlots())
async def process_add_time_study(callback: CallbackQuery, week_date_str: str,
                                 student: Student, page: int, dict_lessons):
    # В зависимости от режима пенальти печатаем по-разному:
    if student.teacher.penalty:
        text = LEXICON_STUDENT['choose_slot_penalty'].format(student.teacher.penalty)
    else:
        text = LEXICON_STUDENT['choose_slot']
    await callback.message.edit_text(text=text,
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page
                                     ))


# Движемся вправо в нашем меню занятий
@router.callback_query(F.data == 'move_right_add', IsMoveRightAddMenu())
async def process_move_right_add_menu(callback: CallbackQuery,
                                      dict_lessons, student: Student,
                                      week_date_str: str, page: int,
                                      state: FSMContext):
    await state.update_data(page=page + 1)
    # В зависимости от режима пенальти печатаем по-разному:
    if student.teacher.penalty:
        text = LEXICON_STUDENT['choose_slot_penalty'].format(student.teacher.penalty)
    else:
        text = LEXICON_STUDENT['choose_slot']
    await callback.message.edit_text(text=text,
                                     reply_markup=create_choose_time_student_kb(
                                         dict_lessons,
                                         week_date_str,
                                         page+1
                                     ))


# Движемся влево в нашем меню занятий
@router.callback_query(F.data == 'move_left_add', IsMoveLeftMenu())
async def process_move_right_add_menu(callback: CallbackQuery, session: AsyncSession, state: FSMContext):

    state_dict = await state.get_data()
    week_date_str = state_dict['week_date']
    week_date = give_date_format_fsm(week_date_str)
    page = state_dict['page'] - 1
    await state.update_data(page=page)

    student = await give_teacher_by_student_id(session,
                                               callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      student.teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date,
                                              student.teacher.penalty)

    # В зависимости от режима пенальти печатаем по-разному:
    if student.teacher.penalty:
        text = LEXICON_STUDENT['choose_slot_penalty'].format(student.teacher.penalty)
    else:
        text = LEXICON_STUDENT['choose_slot']
    await callback.message.edit_text(text=text,
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

    student = await give_teacher_by_student_id(session,
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

    student = await give_teacher_by_student_id(session,
                                               callback.from_user.id)
    lessons_busy = await give_all_busy_time_intervals(session,
                                                      student.teacher_id,
                                                      week_date)

    lessons_week = await give_lessons_week_for_day(session, week_date, student.teacher_id)
    dict_lessons = create_choose_time_student(lessons_week, lessons_busy, week_date,
                                              student.teacher.penalty)
    page = state_dict['page']
    # В зависимости от режима пенальти печатаем по-разному:
    if student.teacher.penalty:
        text = LEXICON_STUDENT['choose_slot_penalty'].format(student.teacher.penalty)
    else:
        text = LEXICON_STUDENT['choose_slot']
    await callback.message.edit_text(text=text,
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
    await callback.answer(text=LEXICON_STUDENT['teacher_not_create_slots'])


# Случай, когда свободных занятий больше нет!
@router.callback_query(F.data == 'add_gap_student', ~IsFreeSlots())
async def process_not_add_time_study(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['not_free_slots'])


###################################### Кнопка УДАЛИТЬ ###########################################

@router.callback_query(F.data == 'remove_gap_student', IsStudentChooseSlots())
async def process_remove_time_study(callback: CallbackQuery,
                                     week_date_str: str, page: int,
                                     all_busy_lessons: list[LessonDay]):

    dict_for_6_lessons = create_delete_time_student(all_busy_lessons)
    await callback.message.edit_text(text=LEXICON_STUDENT['delete_slot'],
                                     reply_markup=create_delete_lessons_menu(
                                        dict_for_6_lessons,
                                        week_date_str,
                                        page)
                                    )


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
    await callback.message.edit_text(text=LEXICON_STUDENT['delete_slot'],
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
    await callback.message.edit_text(text=LEXICON_STUDENT['delete_slot'],
                                     reply_markup=create_delete_lessons_menu(dict_for_6_lessons,
                                                                             week_date_str,
                                                                             page))


# Движение вправо в меню удаления
@router.callback_query(F.data == 'move_right_remove', IsMoveRightRemoveMenu())
async def process_move_left_remove(callback: CallbackQuery, session: AsyncSession,
                                   state: FSMContext,
                                   week_date_str: str,
                                   dict_for_6_lessons,
                                   page: int):
    await state.update_data(page=page+1)

    await callback.message.edit_text(text=LEXICON_STUDENT['delete_slot'],
                                     reply_markup=create_delete_lessons_menu(dict_for_6_lessons,
                                                                             week_date_str,
                                                                             page+1))


# Случай, при нажатии на кнопку __удалить__ нечего удалять
@router.callback_query(F.data == 'remove_gap_student', ~IsStudentChooseSlots())
async def process_not_remove_time_study(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['nothing_remove'])


# Случай, когда мы не можем удалить, потому что время отмены истекло!
@router.callback_query(DeleteFieldCallbackFactory.filter(), ~IsTimeNotExpired())
async def process_not_touch_menu_remove(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['time_delete_expired'])


# Случай, когда нажимаем на пустую кнопку
@router.callback_query(EmptyRemoveFieldCallbackFactory.filter())
async def process_touch_empty_button(callback: CallbackQuery):
    await callback.answer()


# Случай, когда влево двигаться некуда!
@router.callback_query(F.data == 'move_left_remove', ~IsMoveLeftMenu())
async def process_not_move_right_remove(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['can_not_move'])


# Случай, когда двигаться вправо некуда!
@router.callback_query(F.data == 'move_right_remove', ~IsMoveRightRemoveMenu())
async def process_not_move_left_remove(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['can_not_move'])


########################## Кнопка __Мое расписание__ ######################################
# Нажимаем на кнопку Мое расписание и вываливается список доступных дней
@router.callback_query(F.data == 'show_schedule')
async def process_show_schedule(callback: CallbackQuery, state: FSMContext):
    next_seven_days_with_cur = give_list_with_days(datetime.now())

    await callback.message.edit_text(text=LEXICON_STUDENT['my_schedule_menu'],
                                     reply_markup=show_next_seven_days_schedule_kb(*next_seven_days_with_cur))
    await state.clear()


# Выбираем день занятия (нажимаем на этот день)
@router.callback_query(ShowDaysOfScheduleCallbackFactory.filter(), IsLessonsInChoseDay())
async def process_show_lessons_for_day(callback: CallbackQuery,
                                       callback_data: ShowDaysOfScheduleCallbackFactory,
                                       state: FSMContext,
                                       all_lessons_for_day_not_ordered: list[LessonDay]):

    await state.update_data(week_date=callback_data.week_date)

    all_lessons_for_day_ordered_list = show_all_lessons_for_day(all_lessons_for_day_not_ordered)

    await callback.message.edit_text(text=LEXICON_STUDENT['schedule_lesson_day'],
                                     reply_markup=all_lessons_for_day_kb(all_lessons_for_day_ordered_list)
                                     )

#Нечего смотреть в выбранном дне
@router.callback_query(ShowDaysOfScheduleCallbackFactory.filter(), ~IsLessonsInChoseDay())
async def process_not_show_lessons_for_day(callback: CallbackQuery):
    await callback.answer(LEXICON_STUDENT['not_choose_gaps'])


# Нажимаем на временной промежуток, чтобы посмотреть подробную информацию
@router.callback_query(StartEndLessonDayCallbackFactory.filter())
async def process_show_full_information_lesson(callback: CallbackQuery, session: AsyncSession,
                                               callback_data: StartEndLessonDayCallbackFactory,
                                               state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    student = await give_teacher_by_student_id(session,
                                               callback.from_user.id)

    # Проверка на оплату
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)
    information_of_status_lesson = await give_information_of_lesson(session,
                                                                    callback.from_user.id,
                                                                    week_date,
                                                                    lesson_on,
                                                                    lesson_off)

    #Общая информация для определения статуса оплаты и общей суммы занятия
    result_status, counter_lessons = give_result_status_timeinterval(information_of_status_lesson)

    # Получаем информацию об уроке в зависимости от системы пенальти
    text_information_lesson = give_text_information_lesson(student,
                                                           week_date,
                                                           lesson_on,
                                                           lesson_off,
                                                           result_status,
                                                           counter_lessons)

    # Выводим информацию
    await callback.message.edit_text(text=text_information_lesson,
                                     reply_markup=create_button_for_back_to_all_lessons_day(week_date_str,
                                                                                            student,
                                                                                            callback_data.lesson_on,
                                                                                            callback_data.lesson_off,
                                                                                            counter_lessons)
                                     )

##################### Отправляем сообщение преподавателю с ожиданием подтверждения оплаты ############################

#Нажали __отправить__ из меню ученика
@router.callback_query(InformationLessonCallbackFactory.filter(), IsNotAlreadyConfirmed())
async def process_sent_student_payment_confirmation(callback: CallbackQuery, teacher_id: int, bot: Bot,
                                                    session: AsyncSession,
                                                    callback_data: InformationLessonCallbackFactory):
    week_date = give_date_format_fsm(callback_data.week_date)
    student = (await session.execute(select(Student).where(Student.student_id == callback.from_user.id))).scalar()
    await bot.send_message(chat_id=teacher_id,
                           text=LEXICON_STUDENT['sent_student_payment_confirmation']
                           .format(student.name, student.surname,
                                   student.subject, week_date.strftime("%d.%m"),
                                   NUMERIC_DATE[date(year=week_date.year,
                                                     month=week_date.month,
                                                     day=week_date.day).isoweekday()],
                                   callback_data.lesson_on, callback_data.lesson_off,
                                   callback_data.full_price),
                           reply_markup=create_confirm_payment_teacher_kb(callback.from_user.id,
                                                                          callback_data)
                           )
    await callback.answer(text=LEXICON_STUDENT['student_payment_confirmation_good'])

#Случай, когда оплата уже подтверждена
@router.callback_query(InformationLessonCallbackFactory.filter(), ~IsNotAlreadyConfirmed())
async def process_not_sent_student_payment_confirmation(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['already_confirm_lesson'])

#Получаем обратное сообщение с подтверждением (Нажали на кнопку __Ок__)
@router.callback_query(F.data == 'notification_confirmation_student')
async def process_give_repeat_message_confirmation(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

#Нажали __отправить__, так как пришло сообщение о том, что в должниках
@router.callback_query(InformationLessonWithDeleteCallbackFactory.filter(), IsNotAlreadyConfirmed())
async def process_sent_student_payment_confirmation(callback: CallbackQuery, teacher_id: int, bot: Bot,
                                                    session: AsyncSession,
                                                    callback_data: InformationLessonCallbackFactory):
    week_date = give_date_format_fsm(callback_data.week_date)
    student = (await session.execute(select(Student).where(Student.student_id == callback.from_user.id))).scalar()
    await bot.send_message(chat_id=teacher_id,
                           text=LEXICON_STUDENT['sent_student_payment_confirmation']
                           .format(student.name, student.surname,
                                   student.subject, week_date.strftime("%d.%m"),
                                   NUMERIC_DATE[date(year=week_date.year,
                                                     month=week_date.month,
                                                     day=week_date.day).isoweekday()],
                                   callback_data.lesson_on, callback_data.lesson_off,
                                   callback_data.full_price),
                           reply_markup=create_confirm_payment_teacher_kb(callback.from_user.id,
                                                                          callback_data)
                           )
    await callback.answer(text=LEXICON_STUDENT['student_payment_confirmation_good'])
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)


######################################### Нажимаем __ОТМЕНИТЬ__ занятие ######################################
@router.callback_query(RemoveDayOfScheduleCallbackFactory.filter())
async def process_remove_lesson_student(callback: CallbackQuery, bot: Bot, session: AsyncSession,
                                        callback_data: RemoveDayOfScheduleCallbackFactory):

    student = await give_teacher_by_student_id(session, callback.from_user.id)
    lesson_on_time = give_time_format_fsm(callback_data.lesson_on)
    lesson_off_time = give_time_format_fsm(callback_data.lesson_off)
    week_date_date = give_date_format_fsm(callback_data.week_date)

    ######### Удаляем интервалы из таблицы lessons_day
    await delete_gap_lessons_by_student(session, callback.from_user.id,
                                        week_date_date, lesson_on_time,
                                        lesson_off_time)
    ######### Отображаем обновленную страничку
    all_lessons_for_day_not_ordered = ( await give_all_lessons_for_day(session,
                                       week_date_date,
                                       callback.from_user.id
                                       )
                                      ).all()

    #### Если это была не единственная запись на день, то на обновленную страницу со списком занятий на день
    if all_lessons_for_day_not_ordered:
        all_lessons_for_day_ordered_list = show_all_lessons_for_day(all_lessons_for_day_not_ordered)

        await callback.message.edit_text(text=LEXICON_STUDENT['schedule_lesson_day'],
                                         reply_markup=all_lessons_for_day_kb(all_lessons_for_day_ordered_list)
                                         )
    #### Если это была единственная запись - то пробрасываем в меню выбора дней
    else:
        next_seven_days_with_cur = give_list_with_days(datetime.now())

        await callback.message.edit_text(text=LEXICON_STUDENT['my_schedule_menu'],
                                         reply_markup=show_next_seven_days_schedule_kb(*next_seven_days_with_cur))

    ########## Отправляем информацию об удалении учителю в случае, если время удаления занятия находится в диапазоне дней,
    ########## когда учитель хочет получать информацию
    if is_correct_sent_delete_lesson_for_teacher(student.teacher.days_cancellation_notification, week_date_date):
        await bot.send_message(chat_id=student.teacher_id, text=LEXICON_STUDENT['student_cancellation_lesson']
                               .format(student.name, student.surname, week_date_date.strftime("%m.%d"),
                                       NUMERIC_DATE[date(year=week_date_date.year,
                                                         month=week_date_date.month,
                                                         day=week_date_date.day).isoweekday()],
                                       lesson_on_time.strftime("%H:%M"),
                                       lesson_off_time.strftime("%H:%M")),
                               reply_markup=create_ok_remove_day_schedule_student_kb()
                               )
    await session.commit()


###################################### Кнопка НАСТРОЙКИ #############################################

@router.callback_query(F.data == 'settings_student')
async def process_create_menu_settings(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON_STUDENT['menu_settings'],
                                     reply_markup=create_settings_profile_kb())


# Выбрали __Информация обо мне_
@router.callback_query(F.data == 'my_profile_student')
async def process_show_information_profile(callback: CallbackQuery, session: AsyncSession):
    student = await give_teacher_by_student_id(session,
                                               callback.from_user.id)
    course_class = course_class_choose(student.class_learning,
                                       student.course_learning)
    await callback.message.edit_text(text=LEXICON_STUDENT['information_about_student']
                                     .format(student.name,
                                             student.surname,
                                             student.city,
                                             student.place_study,
                                             course_class,
                                             student.subject,
                                             student.price,
                                             student.until_hour_notification,
                                             student.until_minute_notification),
                                     reply_markup=create_back_to_settings_student_kb())

# Выбрали __Редактировать профиль__
@router.callback_query(F.data == 'edit_profile', StateFilter(default_state))
async def process_change_settings_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON_STUDENT['fill_name'])

    await state.set_state(FSMRegistrationStudentForm.fill_name)

#Нажали на кнопку - ничего не происходит
@router.callback_query(F.data == 'debt_information')
async def process_nothing_debt_information(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(F.data == 'delete_profile')
async def process_delete_profile(callback: CallbackQuery, session: AsyncSession):
    await delete_student_profile(session,
                                 callback.from_user.id)
    await callback.message.edit_text(text=LEXICON_ALL['start'],
                                     reply_markup=create_start_kb())


######################################## Кнопка ПЕНАЛЬТИ #############################################
@router.callback_query(F.data == 'penalties', IsTeacherDidSystemPenalties(), IsStudentHasPenalties(),
                       )
async def process_penalties(callback: CallbackQuery, session: AsyncSession):
    student_penalties = await give_students_penalty(session, callback.from_user.id)

    await callback.message.edit_text(text=LEXICON_STUDENT['penalty_menu']
                                     .format(COUNT_BAN - len(student_penalties)),
                                     reply_markup=create_information_penalties(student_penalties))
####################################### Кнопка Задолженности #########################################
@router.callback_query(F.data == 'debts', IsDebtsStudent())
async def process_debts(callback: CallbackQuery, session: AsyncSession,
                        list_debts):
    await callback.message.edit_text(text=LEXICON_STUDENT['debts_header'],
                                     reply_markup=create_debts_student_kb(list_debts))

# Нет задолженностей
@router.callback_query(F.data == 'debts')
async def not_process_debts(callback: CallbackQuery):
    await callback.answer(text=LEXICON_STUDENT['no_debts'])


#######################################################################################################
# Нажатие на кнопки с информацией - ничего не должно происходить
@router.callback_query(PlugPenaltyStudentCallbackFactory.filter())
async def process_not_penalties(callback: CallbackQuery):
    await callback.answer()


# Случай, когда учитель не включил систему пенальти!
@router.callback_query(F.data == 'penalties', ~IsTeacherDidSystemPenalties())
async def process_not_work_penalties(callback: CallbackQuery):
    await callback.answer(LEXICON_STUDENT['system_off'])


# Случай, когда у ученика нет пенальти!
@router.callback_query(F.data == 'penalties', ~IsStudentHasPenalties())
async def process_not_penalties(callback: CallbackQuery):
    await callback.answer(LEXICON_STUDENT['has_not_penalty'])


# Нажимаем __ОК__, когда пришло уведомление за какое-то время до занятия
@router.callback_query(F.data == 'notice_lesson_certain_time_student')
async def create_notice_lesson_certain_time_student(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)