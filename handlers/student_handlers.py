from datetime import date, datetime, timedelta, time
from pprint import pprint

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import StatesGroup, State, default_state
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from keyboards.student_kb import create_entrance_kb

router = Router()


############################### Логика входа в меню идентификации #######################################

@router.callback_query(F.data == 'student_entrance')
async def process_entrance(callback: CallbackQuery):
    await callback.message.edit_text(text='Это меню идентификации!\n'
                                          'Выбери, что хочешь сделать',
                                     reply_markup=create_entrance_kb())


