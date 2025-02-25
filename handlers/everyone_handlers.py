from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from keyboards.everyone_kb import create_start_kb
from lexicon.lexicon_all import LEXICON_ALL

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
