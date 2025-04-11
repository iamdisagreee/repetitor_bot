import uuid
from datetime import datetime, timedelta, date, time

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import default_state
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq_nats import NATSKeyValueScheduleSource

from callback_factory.student_factories import ChangeStatusOfAddListCallbackFactory, DeleteStudentToStudyCallbackFactory
from callback_factory.teacher_factories import ShowDaysOfPayCallbackFactory, EditStatusPayCallbackFactory, \
    DeleteDayCallbackFactory, ShowDaysOfScheduleTeacherCallbackFactory, ShowInfoDayCallbackFactory, \
    DeleteDayScheduleCallbackFactory, PlugScheduleLessonWeekDayBackFactory, \
    SentMessagePaymentStudentCallbackFactory, DebtorInformationCallbackFactory, RemoveDebtorFromListCallbackFactory, \
    ShowNextSevenDaysCallbackFactory, ScheduleEditTeacherCallbackFactory, SentMessagePaymentStudentDebtorCallbackFactory
from database import Student, LessonWeek
from database.teacher_requests import command_add_teacher, command_add_lesson_week, give_installed_lessons_week, \
    delete_week_day, give_all_lessons_day_by_week_day, change_status_pay_student, \
    give_information_of_one_lesson, delete_lesson, delete_teacher_profile, \
    give_all_students_by_teacher, change_status_entry_student, add_student_id_in_database, \
    delete_student_id_in_database, delete_all_lessons_student, \
    give_status_entry_student, give_student_by_teacher_id, \
    give_teacher_profile_by_teacher_id, delete_all_penalties_student, add_penalty_to_student, delete_penalty_of_student, \
    give_list_debtors, remove_debtor_from_list_by_id, \
    give_student_by_teacher_id_debtors, update_until_time_notification_teacher, update_daily_schedule_mailing_teacher, \
    update_daily_report_mailing_teacher, update_days_cancellation_teacher, remove_debtor_from_list_by_info
from filters.teacher_filters import IsTeacherInDatabase, \
    IsCorrectFormatTime, IsEndBiggerStart, IsDifferenceLessThirtyMinutes, \
    IsConflictWithStart, IsConflictWithEnd, IsLessonWeekInDatabase, \
    IsSomethingToShowSchedule, \
    IsPhoneCorrectInput, IsBankCorrectInput, IsPenaltyCorrectInput, IsInputTimeLongerThanNow, \
    IsNewDayNotNear, TeacherStartFilter, IsSomethingToPay, IsNotTeacherAdd, IsHasTeacherStudents, \
    IsUntilTimeNotification, IsDailyScheduleMailingTime, IsDailyReportMailingTime, \
    IsDaysCancellationNotification, IsDebtorsInDatabase
from fsm.fsm_teacher import FSMRegistrationTeacherForm, FSMRegistrationLessonWeek, FSMAddStudentToStudy, \
    FSMSetUntilTimeNotificationTeacher, FSMSetDailyScheduleMailing, FSMSetDailyReportMailing, \
    FSMSetCancellationNotificationTeacher
from keyboards.everyone_kb import create_start_kb
from keyboards.teacher_kb import create_entrance_kb, create_back_to_entrance_kb, create_authorization_kb, \
    create_back_to_profile_kb, create_add_remove_gap_kb, create_all_records_week_day, \
    show_status_lesson_day_kb, \
    show_schedule_lesson_day_kb, back_to_show_schedule_teacher, back_to_show_or_delete_schedule_teacher, \
    settings_teacher_kb, create_management_students_kb, create_list_add_students_kb, \
    create_back_to_management_students_kb, create_list_delete_students_kb, back_to_settings_kb, \
    create_notification_confirmation_student_kb, create_list_debtors_kb, change_list_debtors_kb, \
    show_variants_edit_notifications_kb, create_congratulations_edit_notifications_kb, create_lessons_week_teacher_kb, \
    create_config_teacher_kb, delete_remove_lesson_by_teacher
from lexicon.lexicon_everyone import LEXICON_ALL
from lexicon.lexicon_teacher import LEXICON_TEACHER
from services.services import give_list_with_days, give_time_format_fsm, give_date_format_fsm, \
    give_list_registrations_str, show_intermediate_information_lesson_day_status, give_result_info, COUNT_BAN, \
    course_class_choose, NUMERIC_DATE, create_scheduled_task_handler, give_week_day_by_week_date
from services.services_taskiq import delete_all_schedules_teacher

# Ученик - ничего не происходит
# Преподаватель - открываем

router = Router()
router.callback_query.filter(TeacherStartFilter())


############################### Логика входа в меню идентификации #######################################
@router.callback_query(F.data == 'teacher_entrance')
async def process_entrance(callback: CallbackQuery):
    teacher_entrance_kb = create_entrance_kb()
    await callback.message.edit_text(text=LEXICON_TEACHER['menu_identification'],
                                     reply_markup=teacher_entrance_kb)


#################################### Логика регистрации учителя #####################################
@router.callback_query(F.data == 'reg_teacher', ~IsTeacherInDatabase())
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
    await state.update_data(bank=message.text.capitalize())

    await message.answer(text=LEXICON_TEACHER['fill_penalty'])
    await state.set_state(FSMRegistrationTeacherForm.fill_penalty)


# Ввели пенальти, просим ввести время, за которое будет приходить уведомление о занятии (ЧАСЫ:МИНУТЫ)
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_penalty), IsPenaltyCorrectInput())
async def process_penalty_sent(message: Message, state: FSMContext, session: AsyncSession):
    await state.update_data(penalty=message.text)
    teacher_form = await state.get_data()
    await state.clear()
    await command_add_teacher(session,
                            message.from_user.id,
                            **teacher_form)
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
async def process_wrong_bank_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_bank'])

# Случай, когда неправильно ввели пенальти
@router.message(StateFilter(FSMRegistrationTeacherForm.fill_penalty))
async def process_wrong_penalty_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_penalty'])

# Случай, когда учитель уже зарегистрирован, но нажал на кнопку регистрации!
@router.callback_query(F.data == 'reg_teacher', IsTeacherInDatabase())
async def process_not_start_registration(callback: CallbackQuery):
    await callback.answer(text=LEXICON_TEACHER['now_registered'])


# Случай, когда учитель не зарегистрирован, но нажал на кнопку авторизации!
@router.callback_query(F.data == 'auth_teacher', ~IsTeacherInDatabase())
async def process_not_start_authorization(callback: CallbackQuery):
    await callback.answer(text=LEXICON_TEACHER['not_registered'])


###################################### Зашли в профиль репетитора #######################################
@router.callback_query(F.data == 'auth_teacher', IsTeacherInDatabase())
async def process_start_authorization(callback: CallbackQuery, session: AsyncSession,
                                      scheduler_storage: NATSKeyValueScheduleSource):
    await callback.message.edit_text(text=LEXICON_TEACHER['main_menu_authorization'],
                                     reply_markup=create_authorization_kb())

##################################################################################################
#####################################     ЗАНЯТИЯ       ##########################################
##################################################################################################
@router.callback_query(F.data == 'lessons_week_teacher')
async def process_show_lessons_week(callback: CallbackQuery):
    next_seven_days_with_cur = give_list_with_days(datetime.now())
    await callback.message.edit_text(text=LEXICON_TEACHER['header_seven_days_teacher'],
                                     reply_markup=create_lessons_week_teacher_kb(next_seven_days_with_cur))


#Поймали конкретный день - выводим, что можно сделать с этим днем
@router.callback_query(ShowNextSevenDaysCallbackFactory.filter())
async def process_menu_config_teacher(callback: CallbackQuery, callback_data: ShowNextSevenDaysCallbackFactory):

    week_date = give_date_format_fsm(callback_data.week_date)
    await callback.message.edit_text(text=LEXICON_TEACHER['header_config_teacher']
                                     .format(week_date.strftime("%d.%m"),
                                             give_week_day_by_week_date(week_date).upper()
                                             ),
                                     reply_markup=create_config_teacher_kb(callback_data.week_date))

################################# Кнопка РЕДАКТИРОВАНИЕ РАСПИСАНИЯ #################################
# Выбираем кнопку __ДОБАВИТЬ__ или __УДАЛИТЬ__ !
@router.callback_query(ScheduleEditTeacherCallbackFactory.filter())
async def process_menu_add_remove(callback: CallbackQuery, state: FSMContext,
                                  callback_data: ScheduleEditTeacherCallbackFactory):
    await state.update_data(week_date=callback_data.week_date)

    await callback.message.edit_text(text=LEXICON_TEACHER['schedule_changes_add_remove'],
                                     reply_markup=create_add_remove_gap_kb(callback_data.week_date))

########################## Случай, когда сработала кнопка __ДОБАВИТЬ__! ######################################
@router.callback_query(F.data == 'add_gap_teacher')
async def process_create_day_schedule(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text=LEXICON_TEACHER['add_time_start']
                                  )
    await state.set_state(FSMRegistrationLessonWeek.fill_work_start)

    await callback.answer()


# Ловим время __Старта__ , запрашиваем время __Окончания__ занятий
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), IsCorrectFormatTime(),
                IsNewDayNotNear(), IsInputTimeLongerThanNow(),
                ~IsConflictWithStart())  # ~IsIncorrectTimeInputWithPenalty())
async def process_time_start_sent(message: Message, state: FSMContext):
    await state.update_data(work_start=message.text)

    await state.set_state(FSMRegistrationLessonWeek.fill_work_end)
    await message.answer(text=LEXICON_TEACHER['add_time_end'])


###### ФИЛЬТРЫ ДЛЯ __СТАРТА__
# Формат времени ЧАСЫ:МИНУТЫ не соблюдаются для старта
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsCorrectFormatTime())
async def process_not_correct_format_time(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_correct_format_time'])


# Случай, когда введенное время >= 23:30
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsNewDayNotNear())
async def process_new_day_not_near(message: Message):
    await message.answer(text=LEXICON_TEACHER['new_day_not_near'])


# Случай, когда вводимое время уже наступило!
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), ~IsInputTimeLongerThanNow())
async def process_time_has_passed(message: Message):
    await message.answer(text=LEXICON_TEACHER['time_has_passed'])


# В нашем случае сработало: время старта - время пенальти >= текущего времени сработала
# @router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), IsIncorrectTimeInputWithPenalty())
# async def process_new_day_not_near(message: Message, dt_to_penalty: datetime,
#                                    dt_put: datetime, time_penalty: time):
#     await message.answer(LEXICON_TEACHER['conflict_with_penalty']
#                          .format(dt_put.strftime("%m.%d %H:%M"),
#                                  dt_to_penalty.strftime("%m.%d %H:%M"),
#                                  time_penalty,
#                                  )
#                          )


# Случай, когда стартовое время уже лежит в заданном диапазоне
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_start), IsConflictWithStart())
async def process_start_in_range(message: Message, res_time: list[LessonWeek]):
    res_time_str = give_list_registrations_str(res_time)
    await message.answer(text=LEXICON_TEACHER['start_conflict_with_existing']
                         .format(res_time_str, message.text))


###### КОНЕЦ ФИЛЬТРОВ  ДЛЯ __СТАРТА__

# Случай успешного ввода времени (поймали апдейт конца занятий)
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsCorrectFormatTime(),
                ~IsEndBiggerStart(),
                ~IsDifferenceLessThirtyMinutes(), ~IsConflictWithEnd())
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


# Случай, когда время старта >= время_окончания
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsEndBiggerStart())
async def process_not_thirty_difference(message: Message, work_start: time):
    await message.answer(LEXICON_TEACHER['end_bigger_start'].format(work_start.strftime("%H:%M")))


# Случай, когда время работы меньше 30 минут
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsDifferenceLessThirtyMinutes())
async def process_not_thirty_difference(message: Message, work_start: time):
    await message.answer(text=LEXICON_TEACHER['not_difference_thirty_min']
                         .format(work_start.strftime("%H:%M")))


# Случай, когда время конца занятий уже лежит в заданном диапазоне
@router.message(StateFilter(FSMRegistrationLessonWeek.fill_work_end), IsConflictWithEnd())
async def process_start_in_range(message: Message, work_start: time,
                                 work_end: time,
                                 res_time: list[LessonWeek]):
    res_time_str = give_list_registrations_str(res_time)
    await message.answer(LEXICON_TEACHER['end_conflict_with_existing']
                         .format(res_time_str,
                                 work_start.strftime("%H:%M"),
                                 work_end.strftime("%H:%M")
                                 )
                         )


###########КОНЕЦ ФИЛЬТРОВ ДЛЯ ОКОНЧАНИЯ ЗАНЯТИЙ

########################## Случай, когда сработала кнопка __УДАЛИТЬ__! ######################################
@router.callback_query(F.data == 'remove_gap_teacher', IsLessonWeekInDatabase())
async def process_create_day_schedule_delete(callback: CallbackQuery, session: AsyncSession,
                                             week_date: date):
    weeks_days = await give_installed_lessons_week(session,
                                                   callback.from_user.id,
                                                   week_date)

    await callback.message.edit_text(text=LEXICON_TEACHER['delete_time_start'],
                                     reply_markup=create_all_records_week_day(weeks_days,
                                                                              str(week_date)))


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
    await state.clear()

    await callback.message.edit_text(text=LEXICON_TEACHER['delete_time_start'],
                                     reply_markup=create_all_records_week_day(weeks_days,
                                                                              week_date_str))


# Случай, когда нечего удалять из созданных промежутков!
@router.callback_query(F.data == 'remove_gap_teacher', ~IsLessonWeekInDatabase())
async def process_create_day_schedule_nothing(callback: CallbackQuery):
    await callback.answer(text=LEXICON_TEACHER['nothing_delete_teacher_time'])


########################### Кнопка __ПОДТВЕРЖДЕНИЕ ОПЛАТЫ__ ########################
# Предоставляем выбор дат для просмотра оплаты
# @router.callback_query(F.data == 'confirmation_pay')
# async def process_confirmation_pay(callback: CallbackQuery):
#     next_seven_days_with_cur = give_list_with_days(datetime.now())
#     await callback.message.edit_text(text=LEXICON_TEACHER['confirmation_pay_menu'],
#                                      reply_markup=show_next_seven_days_pay_kb(*next_seven_days_with_cur))


# Вываливаем список учеников в выбранный день, ❌ - не оплачено; ✅ - оплачено
# Чтобы поменять статус - надо нажать на время!
@router.callback_query(ShowDaysOfPayCallbackFactory.filter(), IsSomethingToPay())
async def process_show_status_student(callback: CallbackQuery, session: AsyncSession,
                                      week_date_str: str, week_date: date):
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
# НАДО ДОБАВИТЬ МЕНЮ???
@router.callback_query(EditStatusPayCallbackFactory.filter())
async def process_edit_status_student(callback: CallbackQuery, session: AsyncSession,
                                      callback_data: EditStatusPayCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)

    # Получаем student_id по id учителя, дате занятия и началу занятия
    student = await give_student_by_teacher_id(session,
                                               callback.from_user.id,
                                               week_date,
                                               lesson_on)
    student_id = student.student_id
    student_name = student.name
    student_surname = student.surname
    teacher_penalty = student.teacher.penalty
    len_penalties = len(student.penalties)
    time_now = datetime.now().time()

    # Меняем статус в базе данных и возвращаем статус
    status_student = await change_status_pay_student(session,
                                                     student.student_id,
                                                     week_date,
                                                     lesson_on,
                                                     lesson_off)

    # Проверка: наступило ли время для пенальти или нет.
    # Если наступило, то добавляем в таблицу penalties.
    # Если количество пенальти == 2, то баним
    # проверяем, что значение пенальти != 0 и ❌ -> ✅

    if teacher_penalty and status_student:

        # Условие, что пенальти наступило
        if timedelta(hours=time_now.hour, minutes=time_now.minute) \
                > timedelta(hours=lesson_on.hour - teacher_penalty,
                            minutes=lesson_on.minute):
            # Случай бана
            if len_penalties == COUNT_BAN:
                await change_status_entry_student(session, student_id)
                await delete_all_lessons_student(session, student_id)
                await delete_all_penalties_student(session, student_id)
                # Выводим данные о человеке с баном!
                await callback.answer(text=LEXICON_TEACHER['student_ban']
                                      .format(student_name, student_surname)
                                      )

            else:
                # Случай добавления пенальти
                await add_penalty_to_student(session,
                                             student_id,
                                             week_date,
                                             lesson_on,
                                             lesson_off)
                await callback.answer(text=LEXICON_TEACHER['student_give_penalty']
                                      .format(student_name, student_surname))

    # проверяем, что значение пенальти != 0 и ✅ -> ❌
    # Еще проверяем, что пенальти наступило!
    elif (teacher_penalty and not status_student and
          timedelta(hours=time_now.hour, minutes=time_now.minute)
          > timedelta(hours=lesson_on.hour - teacher_penalty,
                      minutes=lesson_on.minute)):

        await delete_penalty_of_student(session, student_id)
        await callback.answer(text=LEXICON_TEACHER['student_remove_penalty']
                              .format(student_name, student_surname))

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
@router.callback_query(ShowDaysOfPayCallbackFactory.filter(), ~IsSomethingToPay())
async def process_not_show_status_student(callback: CallbackQuery):
    await callback.answer(LEXICON_TEACHER['nobody_choose_lessons'])


####################### Кнопка __ПОДТВЕРДИТЬ__ при запросе о подтверждении ############################
# Получили сообщение с просьбой подтвердить оплату, учеником НЕ в должниках
@router.callback_query(SentMessagePaymentStudentCallbackFactory.filter())
async def process_change_status_payment_message(callback: CallbackQuery, session: AsyncSession,
                                                callback_data: SentMessagePaymentStudentCallbackFactory,
                                                bot: Bot
                                                ):

    week_date = give_date_format_fsm(callback_data.week_date)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)

    #Меняем статус оплаты ученика
    await change_status_pay_student(session,
                                    callback_data.student_id,
                                    week_date,
                                    lesson_on,
                                    lesson_off)
    #Удаляем сообщение преподавателя
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    #Отправляем сообщение в чат ученику
    await bot.send_message(chat_id=callback_data.student_id,
                           text=LEXICON_TEACHER['success_lesson_paid']
                           .format(week_date.strftime("%d.%m"),
                                   NUMERIC_DATE[date(year=week_date.year,
                                                     month=week_date.month,
                                                     day=week_date.day).isoweekday()],
                                   callback_data.lesson_on,
                                   callback_data.lesson_off
                                   ),
                           reply_markup=create_notification_confirmation_student_kb()
                           )

# Получили сообщение с просьбой подтвердить оплату, учеником В должниках
@router.callback_query(SentMessagePaymentStudentDebtorCallbackFactory.filter())
async def process_change_status_payment_message(callback: CallbackQuery, session: AsyncSession,
                                                callback_data: SentMessagePaymentStudentDebtorCallbackFactory,
                                                bot: Bot
                                                ):

    week_date = give_date_format_fsm(callback_data.week_date)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)

    # Удаляем ученика из должников
    await remove_debtor_from_list_by_info(session,
                                        int(callback_data.student_id),
                                        week_date,
                                        lesson_on,
                                        lesson_off)
    #Удаляем сообщение преподавателя
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    #Отправляем сообщение в чат ученику
    await bot.send_message(chat_id=callback_data.student_id,
                           text=LEXICON_TEACHER['success_remove_from_debts']
                           .format(week_date.strftime("%d.%m"),
                                   NUMERIC_DATE[date(year=week_date.year,
                                                     month=week_date.month,
                                                     day=week_date.day).isoweekday()],
                                   callback_data.lesson_on,
                                   callback_data.lesson_off
                                   ),
                           reply_markup=create_notification_confirmation_student_kb()
                           )
    await callback.answer(LEXICON_TEACHER['remove_from_debtors'])
########################################## кнопка МОЕ РАСПИСАНИЕ ######################################
# @router.callback_query(F.data == 'schedule_show')
# async def process_show_my_schedule(callback: CallbackQuery):
#     next_seven_days_with_cur = give_list_with_days(datetime.now())
#     await callback.message.edit_text(text=LEXICON_TEACHER['my_schedule_menu'],
#                                      reply_markup=show_next_seven_days_schedule_teacher_kb(
#                                          *next_seven_days_with_cur)
#                                      )


# Ловим апдейт с конкретным днем, и показываем все временные промежутки за день
@router.callback_query(ShowDaysOfScheduleTeacherCallbackFactory.filter(), IsSomethingToShowSchedule())
async def process_show_schedule_teacher(callback: CallbackQuery, session: AsyncSession,
                                        list_lessons_not_formatted: list[LessonWeek],
                                        week_date_str: str):
    week_date = give_date_format_fsm(week_date_str)

    intermediate_buttons = show_intermediate_information_lesson_day_status(list_lessons_not_formatted)
    await callback.message.edit_text(text=LEXICON_TEACHER['schedule_lesson_day']
                                     .format(week_date.strftime("%d.%m"),
                                             give_week_day_by_week_date(week_date)),
                                     reply_markup=await show_schedule_lesson_day_kb(session,
                                                                                    intermediate_buttons,
                                                                                    week_date_str)
                                     )


# Ловим апдейт и показываем информацию о конкретном промежутке
@router.callback_query(ShowInfoDayCallbackFactory.filter())
async def process_show_lesson_info(callback: CallbackQuery, session: AsyncSession,
                                   callback_data: ShowInfoDayCallbackFactory):
    week_date_str = callback_data.week_date
    week_date = give_date_format_fsm(week_date_str)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)
    price = callback_data.price

    lesson_day = await give_information_of_one_lesson(session,
                                                      callback.from_user.id,
                                                      week_date,
                                                      lesson_on,
                                                      lesson_off)

    course_class = course_class_choose(lesson_day.student.class_learning,
                                       lesson_day.student.course_learning)
    paid_not_paid = give_result_info(callback_data.status)

    await callback.message.edit_text(text=LEXICON_TEACHER['information_student_lesson_day']
                                     .format(lesson_day.student.name,
                                             lesson_day.student.surname,
                                             lesson_day.student.city,
                                             lesson_day.student.place_study,
                                             course_class,
                                             lesson_day.student.subject,
                                             price,
                                             paid_not_paid),
                                     reply_markup=back_to_show_or_delete_schedule_teacher
                                     (week_date_str,
                                      callback_data.lesson_on,
                                      callback_data.lesson_off,
                                      lesson_day.student_id
                                      )
                                     )


# Нажали на кнопку, в которой нет информации об ученике
@router.callback_query(PlugScheduleLessonWeekDayBackFactory.filter())
async def process_show_lesson_nothing(callback: CallbackQuery):
    await callback.answer(LEXICON_TEACHER['show_lesson_nothing'])


# Случай, когда не выставили время
@router.callback_query(ShowDaysOfScheduleTeacherCallbackFactory.filter(), ~IsSomethingToShowSchedule())
async def process_show_schedule_teacher(callback: CallbackQuery):
    await callback.answer(text=LEXICON_TEACHER['teacher_create_slot'])


################################ Нажали на кнопку __удалить__ в информации о дне ###################
@router.callback_query(DeleteDayScheduleCallbackFactory.filter())
async def process_delete_lesson(callback: CallbackQuery, session: AsyncSession, bot: Bot,
                                callback_data: DeleteDayScheduleCallbackFactory):
    week_date = give_date_format_fsm(callback_data.week_date)
    lesson_on = give_time_format_fsm(callback_data.lesson_on)
    lesson_off = give_time_format_fsm(callback_data.lesson_off)

    await delete_lesson(session,
                        week_date,
                        lesson_on,
                        lesson_off)
    # Отправляем сообщение ученику
    await bot.send_message(chat_id=callback_data.student_id,
                           text=LEXICON_TEACHER['send_delete_lesson_student']
                           .format(week_date.strftime("%d.%m"),
                                   give_week_day_by_week_date(week_date),
                                   callback_data.lesson_on,
                                   callback_data.lesson_off),
                           reply_markup=delete_remove_lesson_by_teacher()
                           )

    await callback.message.edit_text(text=LEXICON_TEACHER['success_delete_lesson'],
                                     reply_markup=back_to_show_schedule_teacher(callback_data.week_date))
    await callback.answer(text=LEXICON_TEACHER['notification_delete_sent'])


########################################## Кнопка __Настройки__ в главном меню ################################
@router.callback_query(F.data == 'settings_teacher')
async def process_show_settings(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON_TEACHER['menu_settings'],
                                     reply_markup=settings_teacher_kb())


# Нажали на кнопку __Информация обо мне__
@router.callback_query(F.data == 'my_profile')
async def process_show_teacher_profile(callback: CallbackQuery, session: AsyncSession):
    teacher = await give_teacher_profile_by_teacher_id(session,
                                                       callback.from_user.id)
    until_hour_notification = teacher.until_hour_notification if teacher.until_hour_notification else '-'
    until_minute_notification = teacher.until_minute_notification if teacher.until_minute_notification else '-'
    daily_schedule_mailing_time = teacher.daily_schedule_mailing_time.strftime("%H:%M") if \
        teacher.daily_schedule_mailing_time else '-'
    daily_report_mailing_time = teacher.daily_report_mailing_time.strftime("%H:%M") if \
        teacher.daily_report_mailing_time else '-'
    days_cancellation_notification = teacher.days_cancellation_notification if \
        teacher.days_cancellation_notification else '-'

    await callback.message.edit_text(text=LEXICON_TEACHER['information_about_teacher']
                                     .format(teacher.surname,
                                             teacher.name,
                                             teacher.phone,
                                             teacher.bank,
                                             until_hour_notification,
                                             until_minute_notification,
                                             daily_schedule_mailing_time,
                                             daily_report_mailing_time,
                                             days_cancellation_notification,
                                             ),
                                     reply_markup=back_to_settings_kb())

# Нажали на кнопку ___________________Настройка уведомлений_______________________________
@router.callback_query(F.data == 'notifications_teacher')
async def process_edit_notifications(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON_TEACHER['header_notifications'],
                                     reply_markup=show_variants_edit_notifications_kb())

# Нажали на _Уведомление о занятии_
@router.callback_query(F.data == 'set_until_time_notification')
async def process_set_until_time_notification(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMSetUntilTimeNotificationTeacher.fill_until_time_notification)
    await callback.message.answer(text=LEXICON_TEACHER['fill_until_time_notification'])
    await callback.answer()

# Ловим время ввода _Уведомления о занятии_
@router.message(StateFilter(FSMSetUntilTimeNotificationTeacher.fill_until_time_notification),
                                   IsUntilTimeNotification())
async def process_give_until_time_notification(message: Message, state: FSMContext,
                                               session: AsyncSession):
    await state.clear()
    hour, minute = [int(el) for el in message.text.split(":")]
    await update_until_time_notification_teacher(session,
                                                 message.from_user.id,
                                                 hour,
                                                 minute)
    await message.answer(LEXICON_TEACHER['congratulations_edit_notices'],
                         reply_markup=create_congratulations_edit_notifications_kb())


# Нажали на _Ежедневная отправка расписания_
@router.callback_query(F.data == 'set_daily_schedule_mailing_time')
async def process_set_daily_schedule(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMSetDailyScheduleMailing.fill_daily_schedule_mailing_time)
    await callback.message.answer(text=LEXICON_TEACHER['fill_daily_schedule_mailing_time'])
    await callback.answer()


# Ловим время ввода _Ежедневная отправка расписания_
@router.message(StateFilter(FSMSetDailyScheduleMailing.fill_daily_schedule_mailing_time),
                                   IsDailyScheduleMailingTime())
async def process_give_daily_schedule(message: Message, state: FSMContext,
                                               session: AsyncSession):
    await state.clear()
    hour, minute = [int(el) for el in message.text.split(":")]
    await update_daily_schedule_mailing_teacher(session,
                                                message.from_user.id,
                                                time(hour=hour, minute=minute))

    await create_scheduled_task_handler(task_name='daily_schedule_mailing_teacher',
                                        kwargs={'teacher_id': message.from_user.id},
                                        schedule_id=f'd_s_t_{message.from_user.id}',
                                        cron=f'{minute} {hour} * * *')
    await message.answer(LEXICON_TEACHER['congratulations_edit_notices'],
                         reply_markup=create_congratulations_edit_notifications_kb())



# Нажали на _Отправка отчета за день_
@router.callback_query(F.data == 'set_daily_report_mailing_time')
async def process_set_daily_report(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMSetDailyReportMailing.fill_daily_report_mailing_time)
    await callback.message.answer(text=LEXICON_TEACHER['fill_daily_report_mailing_time'])
    await callback.answer()

# Ловим время ввода _Отправка отчета за день_
@router.message(StateFilter(FSMSetDailyReportMailing.fill_daily_report_mailing_time),
                                   IsDailyReportMailingTime())
async def process_give_daily_report(message: Message, state: FSMContext,
                                               session: AsyncSession):
    await state.clear()
    hour, minute = [int(el) for el in message.text.split(":")]
    await update_daily_report_mailing_teacher(session,
                                                message.from_user.id,
                                                time(hour=hour, minute=minute))

    await create_scheduled_task_handler(task_name='daily_report_mailing_teacher',
                                        kwargs={'teacher_id': message.from_user.id},
                                        schedule_id=f'd_r_t_{message.from_user.id}',
                                        cron=f'{minute} {hour} * * *')
    await message.answer(LEXICON_TEACHER['congratulations_edit_notices'],
                         reply_markup=create_congratulations_edit_notifications_kb())

#Нажали на __Уведомления об отмене занятий__
@router.callback_query(F.data == 'set_cancellation_notification')
async def process_set_cancellation_notification(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMSetCancellationNotificationTeacher.fill_cancellation_notification)
    await callback.message.answer(text=LEXICON_TEACHER['fill_cancellation_notification'])
    await callback.answer()

#Ловим значение __Уведомления об отмене занятий__
@router.message(StateFilter(FSMSetCancellationNotificationTeacher.fill_cancellation_notification),
                IsDaysCancellationNotification())
async def process_give_cancellation_notification(message: Message, state: FSMContext,
                                                 session: AsyncSession):
    await state.clear()
    await update_days_cancellation_teacher(session,
                                           message.from_user.id,
                                           int(message.text))
    await message.answer(LEXICON_TEACHER['congratulations_edit_notices'],
                         reply_markup=create_congratulations_edit_notifications_kb())

# Случай, когда неправильно ввели время уведомления до занятия
@router.message(StateFilter(FSMSetUntilTimeNotificationTeacher.fill_until_time_notification))
async def process_wrong_until_time_notification_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_until_time_notification'])

# Случай, когда неправильно ввели время для ежедневной отправки расписания
@router.message(StateFilter(FSMSetDailyScheduleMailing.fill_daily_schedule_mailing_time))
async def process_wrong_daily_schedule_mailing_time_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_daily_schedule_mailing_time'])

# Случай, когда неправильно ввели время для отчета за день
@router.message(StateFilter(FSMSetDailyReportMailing.fill_daily_report_mailing_time))
async def process_wrong_daily_report_mailing_time_sent(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_daily_report_mailing_time'])

# Случай, когда неправильно кол-во дней для уведомлений об удалении
@router.message(StateFilter(FSMSetCancellationNotificationTeacher.fill_cancellation_notification))
async def process_wrong_give_cancellation_notification(message: Message):
    await message.answer(text=LEXICON_TEACHER['not_fill_cancellation_notification'])


# ------------------------------------------------------------------------------------------------- #

# Нажали на кнопку __Заполнить профиль заново__
@router.callback_query(F.data == 'edit_profile')
async def process_restart_registration(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON_TEACHER['fill_name'],
                                     )
    await state.clear()
    await state.set_state(FSMRegistrationTeacherForm.fill_name)


# Нажали на кнопку __Удалить профиль__
@router.callback_query(F.data == 'delete_profile')
async def process_delete_profile(callback: CallbackQuery, session: AsyncSession):
    await delete_teacher_profile(session,
                                 callback.from_user.id)
    # Удаляем все таски у ученика
    await delete_all_schedules_teacher(callback.from_user.id)
    await callback.message.edit_text(text=LEXICON_ALL['start'],
                                     reply_markup=create_start_kb())


##################################### Управление учениками ###############################################

@router.callback_query(F.data == 'management_students')
async def process_management_students(callback: CallbackQuery):
    await callback.message.edit_text(text=LEXICON_TEACHER['student_management_menu'],
                                     reply_markup=create_management_students_kb())


############################### Список добавленных студентов и их статус: '🔒'/ '🔑' #############################
@router.callback_query(F.data == 'list_add_students', IsHasTeacherStudents())
async def process_list_add_students(callback: CallbackQuery,
                                    list_students: list[Student]):
    await callback.message.edit_text(text=LEXICON_TEACHER['teacher_students'],
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

    await callback.message.edit_text(text=LEXICON_TEACHER['teacher_students'],
                                     reply_markup=create_list_add_students_kb(list_students))


# Случай, когда у учителя нет зарегистрированных учеников
@router.callback_query(F.data == 'list_add_students', ~IsHasTeacherStudents())
async def process_list_not_add_students(callback: CallbackQuery):
    await callback.answer(LEXICON_TEACHER['has_not_students'])


############## Кнопка редактировать (тут можно удалять) ################
@router.callback_query(F.data == 'delete_student_by_teacher')
async def process_show_delete_student_by_teacher(callback: CallbackQuery, session: AsyncSession):
    list_students = await give_all_students_by_teacher(session,
                                                       callback.from_user.id)
    await callback.message.edit_text(text=LEXICON_TEACHER['delete_student_by_teacher'],
                                     reply_markup=create_list_delete_students_kb(list_students))


# Ловим айдишник удаления
@router.callback_query(DeleteStudentToStudyCallbackFactory.filter())
async def process_show_delete_student_by_teacher(callback: CallbackQuery, session: AsyncSession,
                                                 callback_data: DeleteStudentToStudyCallbackFactory):
    await delete_student_id_in_database(session,
                                        callback_data.student_id)

    list_students = await give_all_students_by_teacher(session,
                                                       callback.from_user.id)

    await callback.message.edit_text(text=LEXICON_TEACHER['delete_student_by_teacher'],
                                     reply_markup=create_list_delete_students_kb(list_students))


######################################### Кнопка добавить ученика ####################################3
@router.callback_query(F.data == 'allow_student', StateFilter(default_state))
async def process_add_student_to_study(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON_TEACHER['input_student_id'])
    await state.set_state(FSMAddStudentToStudy.fill_id)


# Ловим введенный айдишник!
@router.message(StateFilter(FSMAddStudentToStudy.fill_id), F.text.isdigit(), IsNotTeacherAdd())
async def process_not_digit_id_sent(message: Message, session: AsyncSession, state: FSMContext):
    await add_student_id_in_database(session,
                                     int(message.text)
                                     )
    await state.clear()
    await message.answer(text=LEXICON_TEACHER['success_added'],
                         reply_markup=create_back_to_management_students_kb())


# Неправильный формат айди!
@router.message(StateFilter(FSMAddStudentToStudy.fill_id), ~F.text.isdigit())
async def process_id_not_sent(message: Message):
    await message.answer(LEXICON_TEACHER['not_success_added_id'])


# Введенный айди это айди учителя!
@router.message(StateFilter(FSMAddStudentToStudy.fill_id), ~IsNotTeacherAdd())
async def process_teacher_sent(message: Message):
    await message.answer(LEXICON_TEACHER['not_success_added_teacher'])


################################ Кнопка __Список должников__ #################################################
# @router.callback_query(F.data == 'list_debtors', IsPenalty())
# async def process_show_list_debtors(callback: CallbackQuery, session: AsyncSession):
#     list_students = await give_all_students_by_teacher_penalties(session,
#                                                                  callback.from_user.id)
#
#     await callback.message.edit_text(text='Здесь вы увидите должников и их данные',
#                                      reply_markup=show_list_of_debtors_kb(list_students))
#
#
# # У ученика нет пенальти!
# @router.callback_query(F.data == 'list_debtors', ~IsPenalty())
# async def process_show_list_debtors(callback: CallbackQuery):
#     await callback.answer(text=LEXICON_TEACHER['system_off'])
#
#
# # Кнопка с данными о пенальти
# @router.callback_query(PlugPenaltyTeacherCallbackFactory.filter())
# async def process_show_list_debtors_plug(callback):
#     await callback.answer()

# Список всех должников
@router.callback_query(F.data == 'list_debtors', IsDebtorsInDatabase())
async def process_show_list_debtors(callback: CallbackQuery,
                                    list_debtors):
    await callback.message.edit_text(text=LEXICON_TEACHER['debtors_start_page'],
                                     reply_markup=create_list_debtors_kb(list_debtors))

# Подробная информация о должнике
@router.callback_query(DebtorInformationCallbackFactory.filter())
async def process_show_full_debtor_information(callback: CallbackQuery, session: AsyncSession,
                                               callback_data: DebtorInformationCallbackFactory):
    week_date=give_date_format_fsm(callback_data.week_date)
    lesson_on=give_time_format_fsm(callback_data.lesson_on)
    lesson_off=give_time_format_fsm(callback_data.lesson_off)

    student = await give_student_by_teacher_id_debtors(session,
                                                       callback.from_user.id,
                                                       week_date, lesson_on)
    # print(student)
    await callback.answer(text=LEXICON_TEACHER['full_information_debtor']
                          .format(student.name, #Vova
                                  student.surname, #Kharitonov
                                  week_date.strftime("%d.%m"),
                                  lesson_on.strftime("%H:%M"),
                                  lesson_off.strftime("%H:%M"),
                                  callback_data.amount_money),
                          show_alert=True)

#Должиков нет
@router.callback_query(F.data == 'list_debtors')
async def process_show_list_debtors(callback: CallbackQuery):
    await callback.answer(text=LEXICON_TEACHER['not_show_list_debtors'])


#Нажали на кнопку __РЕДАКТИРОВАНИЕ__
@router.callback_query(F.data == 'confirmation_debtors')
async def process_change_list_debtors(callback: CallbackQuery, session: AsyncSession):
    list_debtors = await give_list_debtors(session, callback.from_user.id)
    await callback.message.edit_text(text=LEXICON_TEACHER['change_list_debtors'],
                                     reply_markup=change_list_debtors_kb(list_debtors))

# Ловим на удаление из списка должников
@router.callback_query(RemoveDebtorFromListCallbackFactory.filter())
async def process_remove_debtor(callback: CallbackQuery, session: AsyncSession,
                                callback_data: RemoveDebtorFromListCallbackFactory):
    # Удаляем должника
    await remove_debtor_from_list_by_id(session, uuid.UUID(callback_data.debtor_id))
    # Отображаем обновленный список должников
    list_debtors = await give_list_debtors(session, callback.from_user.id)
    await callback.message.edit_text(text=LEXICON_TEACHER['change_list_debtors'],
                                     reply_markup=change_list_debtors_kb(list_debtors))

############################## НАЖИМАЕМ __ОК__ В ЕЖЕДНЕВНОЙ РАССЫЛКЕ ###################################
@router.callback_query(F.data == 'confirmation_day_teacher')
async def process_confirmation_day_teacher(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)


# Нажимаем __ОК__, когда пришло уведомление за какое-то время до занятия
@router.callback_query(F.data == 'notice_lesson_certain_time_teacher')
async def create_notice_lesson_certain_time_student(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

# Нажимаем __ОК__, когда пришло уведомление об отмене занятия]
@router.callback_query(F.data == 'ok_remove_day_schedule_student')
async def create_ok_remove_day_schedule_student(callback: CallbackQuery, bot: Bot):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)