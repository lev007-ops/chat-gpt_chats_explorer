from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from tgbot.models.models import User

from aiogram.filters import Command


start_router = Router()


@start_router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        from tgbot.handlers.registration import registration
        await registration(message, state)
        return
    await message.answer("Добро пожаловать\n/add_chat - добавить новый чат\n/explore - задать вопрос по чату")
    