from datetime import date

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

from lexicon.lexicon_everyone import LEXICON_MENU, LEXICON_ALL


# Устанавливаем вываливающееся меню
async def set_new_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(
            command=command,
            description=description
        )
        for command, description in LEXICON_MENU.items()
    ]
    await bot.set_my_commands(main_menu_commands)


def create_start_kb():
    buttons = [
        [InlineKeyboardButton(text='Ученик',
                              callback_data='student_entrance')],
        [InlineKeyboardButton(text='Преподаватель',
                              callback_data='teacher_entrance')]
    ]
    start_kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    return start_kb

def create_give_id_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LEXICON_ALL['ok'],
                                  callback_data='remove_my_id'),]
        ]
    )
