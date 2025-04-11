from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.taskiq_requests import give_information_for_day
from keyboards.everyone_kb import create_start_kb, create_give_id_kb
from keyboards.student_kb import create_menu_description_student_kb, create_back_to_menu_settings_student_kb
from keyboards.teacher_kb import create_menu_description_teacher_kb, create_back_to_menu_settings_teacher_kb
from lexicon.lexicon_everyone import LEXICON_ALL
from lexicon.lexicon_student import LEXICON_STUDENT
from lexicon.lexicon_teacher import LEXICON_TEACHER

router = Router()


@router.message(CommandStart())
async def process_start_using_bot(message: Message, state: FSMContext,
                                  ):
    await message.answer(text=LEXICON_ALL['start'],
                         reply_markup=create_start_kb())
    await state.clear()


@router.callback_query(F.data == 'start')
async def process_start_using_bot(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(text=LEXICON_ALL['start'],
                                     reply_markup=create_start_kb())
    await state.clear()

@router.message(Command('give_id'))
async def process_give_id(message: Message):
    await message.answer(LEXICON_ALL['give_id'].
                         format(message.from_user.id),
                         reply_markup=create_give_id_kb())

# Нажали на __ОК__ и удаляем сообщение с id
@router.callback_query(F.data == 'remove_my_id')
async def process_remove_id(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)

###################################### МЕНЮ ИНФОРМАЦИЯ ДЛЯ _УЧЕНИКА_ #############################

@router.message(Command('help_student'))
async def process_help_student(message: Message):
    await message.answer(LEXICON_STUDENT['description_header_student'],
                         reply_markup=create_menu_description_student_kb())

@router.callback_query(F.data == 'help_student')
async def process_help_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_STUDENT['description_header_student'],
                         reply_markup=create_menu_description_student_kb())

@router.callback_query(F.data == 'description_lessons_student')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_STUDENT['description_lessons_student'],
                                     reply_markup=create_back_to_menu_settings_student_kb())

@router.callback_query(F.data == 'description_penalties_student')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_STUDENT['description_penalties_student'],
                                     reply_markup=create_back_to_menu_settings_student_kb())

@router.callback_query(F.data == 'description_debts_student')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_STUDENT['description_debts_student'],
                                     reply_markup=create_back_to_menu_settings_student_kb())

@router.callback_query(F.data == 'description_settings_student')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_STUDENT['description_settings_student'],
                                     reply_markup=create_back_to_menu_settings_student_kb())

@router.callback_query(F.data == 'description_notifications_student')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_STUDENT['description_notifications_student'],
                                     reply_markup=create_back_to_menu_settings_student_kb())

###################################### МЕНЮ ИНФОРМАЦИЯ ДЛЯ _УЧИТЕЛЯ_ #############################

@router.message(Command('help_teacher'))
async def process_help_student(message: Message):
    await message.answer(LEXICON_TEACHER['description_header_teacher'],
                         reply_markup=create_menu_description_teacher_kb())

@router.callback_query(F.data == 'help_teacher')
async def process_help_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_TEACHER['description_header_teacher'],
                         reply_markup=create_menu_description_teacher_kb())

@router.callback_query(F.data == 'description_lessons_week_teacher')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_TEACHER['description_lessons_week_teacher'],
                                     reply_markup=create_back_to_menu_settings_teacher_kb())

@router.callback_query(F.data == 'description_management_students')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_TEACHER['description_management_students'],
                                     reply_markup=create_back_to_menu_settings_teacher_kb())

@router.callback_query(F.data == 'description_settings_teacher')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_TEACHER['description_settings_teacher'],
                                     reply_markup=create_back_to_menu_settings_teacher_kb())
#
@router.callback_query(F.data == 'description_notifications_teacher')
async def process_show_description_lessons_student(callback: CallbackQuery):
    await callback.message.edit_text(LEXICON_TEACHER['description_notifications_teacher'],
                                     reply_markup=create_back_to_menu_settings_teacher_kb())

#####################################################################################################

