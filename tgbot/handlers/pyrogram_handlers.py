from pyrogram.handlers import MessageHandler
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.client import Client
from tgbot.models.models import TelegramMessage, Chat, User
from aiogram import Bot
from tgbot.config import load_config
from tgbot.handlers.explore import parse_chat


async def message_hand(client: Client, message: Message):
    me = client.me
    user = User.get_or_none(User.telegram_id == me.id)
    if user is None:
        return
    username = message.chat.title
    if not username:
        username = (message.chat.first_name + " " +
                    (message.chat.last_name if message.chat.last_name is not None else ""))
    if message.text in ["!!add_chat", "!!update_chat"] and message.from_user.id == me.id:
        m = message
        await message.delete()
        chat = Chat.get_or_none(Chat.user == user,
                                Chat.chat_id == m.chat.id)
        config = load_config()
        bot = Bot(token=config.tg_bot.token)
        if m.text == "!!update_chat":
            if chat is None:
                bot.send_message(me.id, "Чат не добавлен. Добавьте чат командой /add_chat")
                return
            chat.title = username
            chat.save()
            await bot.send_message(me.id, f"Чат {username} обновлен")
            return
        if chat is None:
            m1 = await bot.send_message(me.id, "Начинаю добавление чата")
            await parse_chat(m.chat, user, m1, client, username)
        else:
            await bot.send_message(me.id, "Чат уже добавлен")
        return
    chat = Chat.get_or_none(Chat.user == user,
                            Chat.chat_id == message.chat.id)
    if chat is None:
        return
    my_id = me.id
    user = User.get_or_none(User.telegram_id == my_id)
    if user is None:
        return
    m = TelegramMessage.create(
        chat=chat,
        user_parse=user,
        from_user_id=message.from_user.id,
        username=username,
        datetime=message.date,
        text=message.text,
        message_id=message.id
    )
    m.save()


def get_message_handler():
    return MessageHandler(
        message_hand,
        filters=((filters.private | filters.group) & filters.text)
    )
