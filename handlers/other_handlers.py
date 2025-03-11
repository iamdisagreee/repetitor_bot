from aiogram import Router
from aiogram.types import Message

from lexicon.lexicon_all import LEXICON_ALL

router = Router()


# Ввели что-то не то
@router.message()
async def process_incorrect_input(message: Message):
    print(repr(message.text))
    await message.answer(text=LEXICON_ALL['incorrect_input'])
