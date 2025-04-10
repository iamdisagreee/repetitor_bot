from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from database.taskiq_requests import give_information_for_day
from keyboards.everyone_kb import create_start_kb, create_give_id_kb
from lexicon.lexicon_everyone import LEXICON_ALL

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


@router.message(Command('help_student'))
async def process_help_student(message: Message):
    await message.answer(LEXICON_ALL['help_student'])


@router.message(Command('help_teacher'))
async def process_help_student(message: Message):
    await message.answer(LEXICON_ALL['help_teacher'])

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