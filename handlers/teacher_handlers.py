from datetime import date, datetime, timedelta, time
from pprint import pprint

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from callback_factory.student import ChangeStatusOfAddListCallbackFactory, DeleteStudentToStudyCallbackFactory
from callback_factory.teacher import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory, \
    DeleteDayCallbackFactory, ShowDaysOfScheduleTeacherCallbackFactory, ShowInfoDayCallbackFactory, \
    DeleteDayScheduleCallbackFactory, PlugPenaltyTeacherCallbackFactory
from database import Student, LessonDay
from database.models import Penalty
from database.student_requirements import delete_student_profile
from database.teacher_requirements import command_add_teacher, command_add_lesson_week, give_installed_lessons_week, \
    delete_week_day, give_all_lessons_day_by_week_day, change_status_pay_student, \
    give_information_of_one_lesson, delete_lesson, delete_teacher_profile, give_student_id_by_teacher_id, \
    give_penalty_by_teacher_id, give_all_students_by_teacher, change_status_entry_student, add_student_id_in_database, \
    delete_student_id_in_database, give_all_students_by_teacher_penalties, delete_all_lessons_student, \
    give_status_entry_student, give_student_by_teacher_id
from filters.teacher_filters import IsTeacherInDatabase, \
    FindNextSevenDaysFromKeyboard, IsCorrectFormatTime, IsNoEndBiggerStart, IsDifferenceThirtyMinutes, \
    IsNoConflictWithStart, IsNoConflictWithEnd, IsRemoveNameRight, IsLessonWeekInDatabaseState, IsSomethingToConfirm, \
    IsPenaltyNow, IsPhoneCorrectInput, IsBankCorrectInput, IsPenaltyCorrectInput, IsInputTimeLongerThanNow, \
    IsNewDayNotNear, IsCorrectTimeInputWithPenalty
from keyboards.everyone_kb import create_start_kb
from keyboards.teacher_kb import create_entrance_kb, create_back_to_entrance_kb, create_authorization_kb, \
    show_next_seven_days_kb, create_back_to_profile_kb, create_add_remove_gap_kb, create_all_records_week_day, \
    show_next_seven_days_pay_kb, show_status_lesson_day_kb, show_next_seven_days_schedule_teacher_kb, \
    show_schedule_lesson_day_kb, back_to_show_schedule_teacher, back_to_show_or_delete_schedule_teacher, \
    settings_teacher_kb, create_management_students_kb, create_list_add_students_kb, \
    create_back_to_management_students_kb, create_list_delete_students_kb, show_list_of_debtors_kb
from lexicon.lexicon_teacher import LEXICON_TEACHER
from services.services import give_list_with_days, give_time_format_fsm, give_date_format_fsm, \
    give_list_registrations_str, show_intermediate_information_lesson_day_status, give_result_info, COUNT_BAN

router = Router()


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


# @router.message(Command(commands='cancel'))
# async def process_restart_state(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer("Состояние очищено!")


############################### Логика входа в меню идентификации #######################################
@router.callback_query(F.data == 'teacher_entrance')
async def process_entrance(callback: CallbackQuery):
    teacher_entrance_kb = create_entrance_kb()
    await callback.message.edit_text(text=LEXICON_TEACHER['menu_identification'],
                                     reply_markup=teacher_entrance_kb)


#################################### Логика регистрации учителя #####################################
@router.callback_query(F.data == 'reg_teacher', ~IsTeacherInDatabase(), StateFilter(default_state))
async def process_start_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON_TEACHER['fill_name'],
                                     )
    await state.set_state(FSMRegistrationTeacherForm.fill_name)


# Введено имя, просим ввести фамилию
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_name), F.text.isalpha())
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(name=message.text.capitalize())
    await message.answer(text=LEXICON_TEACHER['fill_surname'])
    await state.set_state(FSMRegistrationTeacherForm.fill_surname)


# Введена фамилия, просим ввести номер телефона
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_surname), F.text.isalpha())
async def process_surname_sent(message: Message, state: FSMContext):
    await state.update_data(surname=message.text.capitalize())
    await message.answer(text=LEXICON_TEACHER['fill_phone'])
    await state.set_state(FSMRegistrationTeacherForm.fill_phone)


# Введен телефон, просим ввести банк/банки
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_phone), IsPhoneCorrectInput())
async def process_phone_sent(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer(text=LEXICON_TEACHER['fill_bank'])
    await state.set_state(FSMRegistrationTeacherForm.fill_bank)


# Введен банк/банки, просим ввести пенальти
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_bank), IsBankCorrectInput())
async def process_bank_sent(message: Message, state: FSMContext):
    await state.update_data(bank=message.text)

    await message.answer(text=LEXICON_TEACHER['fill_penalty'])
    await state.set_state(FSMRegistrationTeacherForm.fill_penalty)


# Ввели пенальти, сохраняем данные и чистим состояние
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_penalty), IsPenaltyCorrectInput())
async def process_bank_sent(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(penalty=message.text)

    teacher_form = await state.get_data()
    await command_add_teacher(session,
                              message.from_user.id,
                              **teacher_form)
    await state.clear()

    await message.answer(text=LEXICON_TEACHER['access_registration_profile'],
                         reply_markup=create_back_to_entrance_kb())


# Случай, когда неправильно ввели имя
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_name))
async def process_wrong_name_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_name'])


# Случай, когда неправильно ввели фамилию
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_surname))
async def process_wrong_surname_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_surname'])


# Случай, когда неправильно ввели номер телефона
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_phone))
async def process_wrong_phone_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_phone'])


# Случай, когда неправильно ввели банк/банки
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_bank))
async def process_wrong_phone_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_bank'])


# Случай, когда неправильно ввели банк/банки
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_bank))
async def process_wrong_phone_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_bank'])


# Случай, когда неправильно ввели пенальти
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_penalty))
async def process_wrong_phone_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_penalty'])


# Случай, когда учитель уже зарегистрирован, но нажал на кнопку регистрации!
@router.callback_query(F.data == 'reg_teacher', IsTeacherInDatabase())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer(text='Вы уже зарегистрированы!')


# Случай, когда учитель не зарегистрирован, но нажал на кнопку авторизации!
@router.callback_query(F.data == 'auth_teacher', ~IsTeacherInDatabase())
async def process_not_start_authorization(message: Message):
    await message.answer(text='Вы еще не зарегистрированы!')


###################################### Зашли в профиль репетитора #######################################
@router.callback_query(F.data == 'auth_teacher', IsTeacherInDatabase())
async def process_start_authorization(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON_TEACHER['main_menu_authorization'],
                                     reply_markup=create_authorization_kb())


################################# Кнопка РЕДАКТИРОВАНИЕ РАСПИСАНИЯ #################################
@router.callback_query(F.data == 'schedule_teacher')
async def process_show_schedule(callback: CallbackQuery):
    next_seven_days_with_cur = give_list_with_days(datetime.now())

    await callback.message.edit_text(text=LEXICON_TEACHER['schedule_teacher_menu'],
                                     reply_markup=show_next_seven_days_kb(next_seven_days_with_cur))


# Выбираем кнопку __ДОБАВИТЬ__ или __УДАЛИТЬ__ !
@router.callback_query(FindNextSevenDaysFromKeyboard())
async def process_menu_add_remove(callback: CallbackQuery, state: FSMContext):
    await state.update_data(week_date=callback.data)

    await callback.message.edit_text(text=LEXICON_TEACHER['schedule_changes_add_remove'],
                                     reply_markup=create_add_remove_gap_kb())


########################## Случай, когда сработала кнока __ДОБАВИТЬ__! ######################################
@router.callback_query(F.data == 'add_gap_teacher', StateFilter(default_state))
async def process_create_day_schedule(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text=LEXICON_TEACHER['add_time_start']
                                  )
    await state.set_state(FSMRegistrationLessonWeek.fill_work_start)

    await callback.answer()


# Ловим время __Старта__ , запрашиваем время __Окончания__ занятий
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), IsCorrectFormatTime(),
                IsNewDayNotNear(), IsInputTimeLongerThanNow(),  # IsCorrectTimeInputWithPenalty(),
                IsNoConflictWithStart())
async def process_time_start_sent(message: Message, state: FSMContext):
    await state.update_data(work_start=message.text)

    await state.set_state(FSMRegistrationLessonWeek.fill_work_end)
    await message.answer(text=LEXICON_TEACHER['add_time_end'])


###### ФИЛЬТРЫ ДЛЯ __СТАРТА__
# Формат времени ЧАСЫ:МИНУТЫ не соблюдаются для старта
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsCorrectFormatTime())
async def process_not_correct_format_time(message: Message):
    await message.answer(LEXICON_TEACHER['not_correct_format_time'])


# Случай, когда введенно время >= 23:30
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsNewDayNotNear())
async def process_new_day_not_near(message: Message):
    await message.answer(LEXICON_TEACHER['new_day_not_near'])


# Случай, когда вводимое время уже наступило!
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsInputTimeLongerThanNow())
async def process_time_has_passed(message: Message):
    await message.answer(LEXICON_TEACHER['time_has_passed'])


# Проверка, что время старта - время пенальти > текущего времени не сработала
# @router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsCorrectTimeInputWithPenalty())
# async def process_new_day_not_near(message: Message, session: AsyncSession,
#                                    state: FSMContext):
#     week_date_str = (await state.get_data())['week_date']
#     week_date = give_date_format_fsm(week_date_str)
#     time_put = give_time_format_fsm(message.text)
#     penalty = await give_penalty_by_teacher_id(session,
#                                                message.from_user.id)
#     dt_put = datetime(year=week_date.year,
#                       month=week_date.month,
#                       day=week_date.day,
#                       hour=time_put.hour,
#                       minute=time_put.minute)
#     await message.answer(LEXICON_TEACHER['conflict_with_penalty']
#                          .format((dt_put - timedelta(hours=penalty)).strftime("%H:%M"),
#                                  time_put.strftime("%H:%M"))
#                          )


# Случай, когда стартовое время уже лежит в заданном диапазоне
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsNoConflictWithStart())
async def process_start_in_range(message: Message, session: AsyncSession, state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    res_time = await give_installed_lessons_week(session,
                                                 message.from_user.id,
                                                 week_date)

    res_time_str = give_list_registrations_str(res_time)
    await message.answer(text=LEXICON_TEACHER['start_conflict_with_existing']
                         .format(res_time_str, message.text))


###### КОНЕЦ ФИЛЬТРОВ  ДЛЯ __СТАРТА__

# Случай успешного ввода времени (поймали апдейт конца занятий)
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsNoEndBiggerStart(),
                IsCorrectFormatTime(),
                IsDifferenceThirtyMinutes(), IsNoConflictWithEnd())
async def process_time_end_sent(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(work_end=message.text)
    lesson_day_form = await state.get_data()

    time_to_repeat = lesson_day_form['week_date']

    lesson_day_form['week_date'] = give_date_format_fsm(lesson_day_form['week_date'])
    lesson_day_form['work_start'] = give_time_format_fsm(lesson_day_form['work_start'])
    lesson_day_form['work_end'] = give_time_format_fsm(lesson_day_form['work_end'])

    await command_add_lesson_week(session,
                                  message.from_user.id,
                                  **lesson_day_form)

    await state.clear()

    await message.answer(text=LEXICON_TEACHER['add_time_start_right'],
                         reply_markup=create_back_to_profile_kb(time_to_repeat)
                         )


##############ФИЛЬТРЫ ДЛЯ ОКОНЧАНИЯ ЗАНЯТИЙ

# Формат времени ЧАСЫ:МИНУТЫ не соблюдаются для окончания
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsCorrectFormatTime())
async def process_not_correct_format(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_correct_format_time']
                         )


# Случай, когда время работы меньше 30 минут
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsDifferenceThirtyMinutes())
async def process_not_thirty_difference(message: Message, state: FSMContext):
    work_start = (await state.get_data())['work_start']
    await message.answer(text=LEXICON_TEACHER['not_difference_thirty_min'].format(work_start))


# Случай, если время конца работы начинается раньше времени старта работы
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsNoEndBiggerStart())
async def process_not_thirty_difference(message: Message, state: FSMContext):
    work_start = (await state.get_data())['work_start']
    await message.answer(LEXICON_TEACHER['end_bigger_start'].format(work_start))


# Случай, когда время конца занятий уже лежит в заданном диапазоне
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), ~IsNoConflictWithEnd())
async def process_start_in_range(message: Message, session: AsyncSession, state: FSMContext):
    data_info = await state.get_data()
    week_date = give_date_format_fsm(data_info['week_date'])

    res_time = await give_installed_lessons_week(session,
                                                 message.from_user.id,
                                                 week_date)
    res_time_str = give_list_registrations_str(res_time)
    await message.answer(LEXICON_TEACHER['end_conflict_with_existing']
                         .format(res_time_str, data_info['work_start']))


###########КОНЕЦ ФИЛЬТРОВ ДЛЯ ОКОНЧАНИЯ ЗАНЯТИЙ

########################## Случай, когда сработала кнока __удалить__! ######################################
@router.callback_query(F.data == 'remove_gap_teacher', IsLessonWeekInDatabaseState())
async def process_create_day_schedule_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    week_date_str = (await state.get_data())['week_date']
    week_date = give_date_format_fsm(week_date_str)

    weeks_days = await give_installed_lessons_week(session,
                                                   callback.from_user.id,
                                                   week_date)

    await callback.message.edit_text(text=LEXICON_TEACHER['delete_time_start'],
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

    await callback.message.edit_text(text=LEXICON_TEACHER['delete_time_start'],
                                     reply_markup=create_all_records_week_day(weeks_days))


# Случай, когда нечего удалять из созданных промежутков!
@router.callback_query(F.data == 'remove_gap_teacher', ~IsLessonWeekInDatabaseState())
async def process_create_day_schedule_nothing(callback: CallbackQuery):
    await callback.answer(text=LEXICON_TEACHER['nothing_delete_teacher_time'])


########################### Кнопка __Подтверждение оплаты__ ########################
# Предоставляем выбор дат для просмотра оплаты
@router.callback_query(F.data == 'confirmation_pay')
async def process_confirmation_pay(callback: CallbackQuery):
    next_seven_days_with_cur = give_list_with_days(datetime.now())
    await callback.message.edit_text(text=LEXICON_TEACHER['confirmation_pay_menu'],
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
    await callback.message.edit_text(text=LEXICON_TEACHER['change_status_pay_menu'],
                                     reply_markup=await show_status_lesson_day_kb(intermediate_buttons,
                                                                                  session,
                                                                                  week_date_str))


# Ловим нажатие на кнопку и меняем статус оплаты: ❌ -> ✅ ; ✅ -> ❌
# Проверяем на условие пенальти:
# ❌ -> ✅ - проверяем на пенальти/баним (если указано время)
# ✅ -> ❌ - не проверяем на пенальти (случайные клики)
# НАДО ДОБАВИТЬ МЕНЮ
@router.callback_query(EditStatusPayCallbackFactory.filter())
async def process_edit_status_student(callback: CallbackQuery, session: AsyncSession,
                                      callback_data: EditStatusPayCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)

    # Получаем student_id по id учителя, дате занятия и началу занятия
    student_id = await give_student_id_by_teacher_id(session,
                                                     callback.from_user.id,
                                                     week_date,
                                                     lesson_on,
                                                     )
    # Меняем статус в базе данных и возвращаем статус
    status_student = await change_status_pay_student(session,
                                                     student_id,
                                                     week_date,
                                                     lesson_on,
                                                     lesson_off)
    #print(status_student)
    # Проверка: наступило ли время для пенальти или нет.
    # Если наступило, то добавляем в таблицу penalties.
    # Если количество пенальти == 2, то баним
    teacher_penalty = await give_penalty_by_teacher_id(session,
                                                       callback.from_user.id)

    # проверяем, что значение пенальти != 0 и ❌ -> ✅
    if teacher_penalty and status_student:
        time_now = time(hour=datetime.now().hour, minute=datetime.now().minute)
        student = await give_student_by_teacher_id(session,
                                                   callback.from_user.id,
                                                   week_date,
                                                   lesson_on)
        #print(status_student)
        # Условие, что пенальти наступило
        if timedelta(hours=time_now.hour, minutes=time_now.minute) \
                > timedelta(hours=lesson_on.hour - teacher_penalty,
                            minutes=lesson_on.minute):
            #print(status_student)
            if len(student.penalties) >= 1:
                #await change_status_entry_student(session, student.student_id)
                student.access.status = False
                to_delete_penalty = delete(Penalty).where(Student.student_id == student.student_id)
                to_delete_lesson_day = delete(LessonDay).where(Student.student_id == student.student_id)
                await session.execute(to_delete_penalty)
                await session.execute(to_delete_lesson_day)
                # Выводим данные о человеке с баном!
                await callback.answer(f'{student.name} {student.surname} забанен!')

            else:
                penalty = Penalty(student_id=student.student_id,
                                  week_date=week_date,
                                  lesson_on=lesson_on,
                                  lesson_off=lesson_off)
                session.add(penalty)
                await callback.answer(f'{student.name} {student.surname} получил пенальти!')
            await session.commit()

    # Выводим нашу клавиатуру снова

    list_lessons_not_formatted = await give_all_lessons_day_by_week_day(session,
                                                                        callback.from_user.id,
                                                                        week_date)

    intermediate_buttons = show_intermediate_information_lesson_day_status(list_lessons_not_formatted)

    await callback.message.edit_text(text=LEXICON_TEACHER['change_status_pay_menu'],
                                     reply_markup=await show_status_lesson_day_kb(intermediate_buttons,
                                                                                  session,
                                                                                  week_date_str))


# Случай, когда никто еще не выбрал занятие! И статус оплаты просто не появился!
@router.callback_query(ShowDaysOfPayCallbackFactory.filter(), ~IsSomethingToConfirm())
async def process_not_show_status_student(callback: CallbackQuery):
    await callback.answer(LEXICON_TEACHER['nobody_choose_lessons'])


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


########################################## Кнопка __Настройки__ в главном меню ################################
@router.callback_query(F.data == 'settings_teacher')
async def process_show_settings(callback: CallbackQuery):
    await callback.message.edit_text(text='Выберите, что хотите сделать!',
                                     reply_markup=settings_teacher_kb())


# Нажали на кнопку Заполнить профиль заново
@router.callback_query(F.data == 'edit_profile')
async def process_restart_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text="Пожалуйста, введите ваше имя!",
                                     )
    await state.set_state(FSMRegistrationTeacherForm.fill_name)


# Нажали на кнопку Удалить профиль
@router.callback_query(F.data == 'delete_profile')
async def process_delete_profile(callback: CallbackQuery, session: AsyncSession):
    await delete_teacher_profile(session,
                                 callback.from_user.id)

    await callback.message.edit_text(text="Здравствуйте, выберите роль!",
                                     reply_markup=create_start_kb())


##################################### Управление учениками ###############################################

@router.callback_query(F.data == 'management_students')
async def process_management_students(callback: CallbackQuery):
    await callback.message.edit_text(text='Выберите, что хотите сделать!',
                                     reply_markup=create_management_students_kb())


############################### Список добавленных студентов и их статус: '🔒'/ '🔑' #############################
@router.callback_query(F.data == 'list_add_students')
async def process_list_add_students(callback: CallbackQuery,
                                    session: AsyncSession):
    list_students = await give_all_students_by_teacher(session,
                                                       callback.from_user.id)

    await callback.message.edit_text(text='Список учеников:',
                                     reply_markup=create_list_add_students_kb(list_students))


# Меняем статус ученика на обратный '🔒' -> '🔑'/ '🔑' -> '🔒'
@router.callback_query(ChangeStatusOfAddListCallbackFactory.filter())
async def process_change_status_entry_student(callback: CallbackQuery, session: AsyncSession,
                                              callback_data: ChangeStatusOfAddListCallbackFactory):
    student_id = callback_data.student_id
    await change_status_entry_student(session, student_id)

    if not (await give_status_entry_student(session,
                                            student_id)):
        await delete_all_lessons_student(session,
                                         student_id)

    list_students = await give_all_students_by_teacher(session,
                                                       callback.from_user.id)

    await callback.message.edit_text(text='Список учеников:',
                                     reply_markup=create_list_add_students_kb(list_students))


############## Кнопка редактировать (тут можно удалять) ################
@router.callback_query(F.data == 'delete_student_by_teacher')
async def process_show_delete_student_by_teacher(callback: CallbackQuery, session: AsyncSession):
    list_students = await give_all_students_by_teacher(session,
                                                       callback.from_user.id)
    await callback.message.edit_text(text='Нажми, чтобы удалить ученика!',
                                     reply_markup=create_list_delete_students_kb(list_students))


# Ловим айдишник удаления
@router.callback_query(DeleteStudentToStudyCallbackFactory.filter())
async def process_show_delete_student_by_teacher(callback: CallbackQuery, session: AsyncSession,
                                                 callback_data: DeleteStudentToStudyCallbackFactory):
    await delete_student_id_in_database(session,
                                        callback_data.student_id)

    list_students = await give_all_students_by_teacher(session,
                                                       callback.from_user.id)

    await callback.message.edit_text(text='Нажми, чтобы удалить ученика!',
                                     reply_markup=create_list_delete_students_kb(list_students))


######################################### Кнопка добавить ученика ####################################3
@router.callback_query(F.data == 'allow_student')
async def process_add_student_to_study(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text='Введите id ученика:')
    await state.set_state(FSMAddStudentToStudy.fill_id)


# Ловим введенный айдишник!
@router.message(StateFilter(FSMAddStudentToStudy.fill_id))
async def process_id_sent(message: Message, session: AsyncSession, state: FSMContext):
    await add_student_id_in_database(session,
                                     int(message.text)
                                     )
    await state.clear()
    await message.answer(text='Ученик успешно добавлен!',
                         reply_markup=create_back_to_management_students_kb())


################################ Кнопка __Список должников__ #################################################
@router.callback_query(F.data == 'list_debtors')
async def process_show_list_debtors(callback: CallbackQuery, session: AsyncSession):
    list_students = await give_all_students_by_teacher_penalties(session,
                                                                 callback.from_user.id)

    await callback.message.edit_text(text='Здесь вы увидите должников и их статистику',
                                     reply_markup=show_list_of_debtors_kb(list_students))


@router.callback_query(PlugPenaltyTeacherCallbackFactory.filter())
async def process_show_list_debtors_plug(callback):
    await callback.answer()
