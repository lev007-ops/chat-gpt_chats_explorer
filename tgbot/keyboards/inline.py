from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_code_keyboard():
    keyboard = InlineKeyboardBuilder()
    buttons = [types.InlineKeyboardButton(
        text=str(i), callback_data=str(i)) for i in range(10)]
    buttons.append(types.InlineKeyboardButton(
        text="⬅️", callback_data="delete"))
    keyboard.row(*buttons, width=3)
    return keyboard
