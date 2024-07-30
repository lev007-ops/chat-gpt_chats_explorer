from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from tgbot.models.models import User, TelegramMessage, Chat

from aiogram.filters import Command
from tgbot.misc.states import ExploreChat, SelectChat
from pyrogram.client import Client
from pyrogram.errors import FloodWait
from pyrogram.types import Dialog, Chat as TGChat
from pyrogram.types import Message as PyrogramMessage
from tgbot.handlers.gpt_methods import get_chat, explain_chat, to_markdown
from tgbot.handlers.gpt_methods import Message as Msg
from random import randint
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from datetime import datetime
import asyncio


explore_router = Router()


@explore_router.message(Command("add_chat"))
async def input_chat(message: Message, state: FSMContext):
    await state.clear()
    user = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        from tgbot.handlers.registration import registration
        await registration(message, state)
        return
    await message.answer("Привет, что бы добавить чат, отправьте в него эту команду, сообщение с командой моментально удалится, и не кто из участников чата его не увидит (команда работает в личных чатах и группах): ```!!add_chat```", parse_mode="Markdown")


async def parse_chat(chat: TGChat, user: User,
                     message: Message, client: Client,
                     title: str):
    try:
        await client.connect()
    except Exception as e:
        pass
    db_chat = Chat.get_or_none(chat_id=chat.id,
                               user=user)
    if db_chat:
        await message.answer("Этот чат уже добавлен")
        return
    db_chat, _ = Chat.get_or_create(
        chat_id=chat.id,
        user=user,
        title=title)
    async for message_p in client.get_chat_history(chat.id):
        message_p: PyrogramMessage
        message_datetime = message_p.date
        if message_p.text is None or message_p.from_user is None:
            continue
        if message_p.from_user.first_name is None:
            first_name = "Unknown"
        else:
            first_name = message_p.from_user.first_name
        text = message_p.text
        if text is None:
            if message_p.caption is not None:
                text = message_p.caption
        if text:
            msg, _ = TelegramMessage.get_or_create(
                chat=db_chat,
                user_parse=user,
                from_user_id=message_p.from_user.id,
                username=first_name + " " +
                (message_p.from_user.last_name if message_p.from_user.last_name is not None else ""),
                datetime=message_datetime,
                text=message_p.text,
                message_id=message_p.id
            )
            msg.save()
    await message.answer("Чат собран, можете задавать вопросы командой /explain")


@ explore_router.message(SelectChat.input_chat)
async def confirm_chat(message: Message, state: FSMContext):
    user: User = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        return
    debug = False
    if message.text == "IDDQD":
        await state.update_data(chat_id=-4120599127)
        debug = True
    if message.text == "Чат найден" or debug:
        data = await state.get_data()
        chat_id = data["chat_id"]
        await message.answer("Начался сбор сообщений, если чат большой - это может занимать ОЧЕНЬ МНОГО времени (больше 24 часов), пожалуйста ожидайте",
                             reply_markup=ReplyKeyboardRemove())
        await parse_chat(chat_id, user, message)
        return
    await message.answer("Обработка запроса",
                         reply_markup=ReplyKeyboardRemove())
    m = await message.answer("Спасибо, начинаю поиск")
    client = Client(f"user_{user.telegram_id}",
                    session_string=user.session_string,
                    in_memory=True)
    ERROR_MESSAGE = "Ошибка подключения к Telegram API, попробуйте зарегестрироваться снова командой /register"

    try:
        await client.connect()
    except ConnectionError:
        await message.answer(ERROR_MESSAGE)
        return
    except FloodWait as e:
        await message.answer(f"Подождите {e.x} секунд и попробуйте снова")
        return
    except Exception as e:
        await message.answer(f"Неизвестная ошибка: {e}")
        return

    dialogs = []
    update_num = randint(50, 100)
    s = 0
    async for dialog in client.get_dialogs():
        dialog: Dialog
        if dialog.chat.type.value in ["private", "group", "supergroup"]:
            title = dialog.chat.title
            if not title:
                if not dialog.chat.first_name:
                    continue
                title = (dialog.chat.first_name + " " +
                         (dialog.chat.last_name if dialog.chat.last_name is not None else ""))
            dialogs.append({"id": dialog.chat.id, "name": title})
            s += 1
            if s == update_num:
                try:
                    await m.edit_text(f"Найдено {len(dialogs)} группы и чатов. Поиск продолжается...")
                except (TelegramRetryAfter, TelegramBadRequest):
                    pass
                s = 0
                update_num = randint(50, 100)
    await m.edit_text(f"Найдено {len(dialogs)} группы и чатов - 100%")
    try:
        chat_id = await get_chat(dialogs, message.text)
    except ValueError:
        await message.answer(
            "Что-то пошло не так, пожалуйста, попробуйте позже")
        return
    if chat_id == 0:
        await message.answer("Чат не найден, попробуйте другой запрос")
        return
    chat = await client.get_chat(chat_id)
    title = chat.title
    if not title:
        title = (chat.first_name + " " +
                 (chat.last_name if chat.last_name is not None else ""))
    ok_keyboard = ReplyKeyboardMarkup(keyboard=[
        [
            KeyboardButton(text="Чат найден")
        ]
    ])
    await message.answer(
        f'Найден чат {title}. Подтвердите его, нажав на кнопку или попробуйте другой запрос',
        reply_markup=ok_keyboard)
    await state.update_data(chat_id=chat.id)


@explore_router.message(Command("explain"))
async def select_chat_to_explain(message: Message, state: FSMContext):
    await state.clear()
    user: User = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        return
    client = Client(f"user_{user.telegram_id}",
                    session_string=user.session_string,
                    in_memory=True)
    chats = Chat.select().where(Chat.user == user)
    if not chats:
        await message.answer("У вас нет добавленных чатов, добавьте их командой /add_chat")
        return
    try:
        await client.connect()
    except ConnectionError:
        await message.answer("Ошибка подключения к Telegram API, попробуйте зарегестрироваться снова командой /register")
        return
    except FloodWait as e:
        await message.answer(f"Подождите {e.x} секунд и попробуйте снова")
        return
    except Exception as e:
        await message.answer(f"Неизвестная ошибка: {e}")
        return
    chats_text = "Ваши чаты:\n"
    chats_list = []
    number = 1
    for chat in chats:
        chat: Chat
        chats_text += f"{number}. {chat.title}\n"
        chats_list.append({"id": chat.chat_id, "name": chat.title,
                           "number": number})
        number += 1
    try:
        await client.disconnect()
    except Exception as e:
        pass
    await state.update_data(chats_list=chats_list)
    keyboard = ReplyKeyboardRemove()
    await message.answer(f"Введи номер чата. Поиск происходит только по чатам, добавленным через команду ```/add_chat```\n{chats_text}\n\n(Если название чата изменилось, отправьте в него команду ```!!update_chat``` и мы обновим его название)", reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(ExploreChat.input_dates)


@explore_router.message(ExploreChat.input_dates)
async def input_dates(message: Message, state: FSMContext):
    user: User = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        return
    await message.answer("Обработка запроса")
    data = await state.get_data()
    chats_list = data.get("chats_list")
    try:
        chat_number = int(message.text)
    except ValueError:
        await message.answer(
            "Номер чата должен быть числом, попробуйте ещё раз")
        return
    if chat_number < 1 or chat_number > len(chats_list):
        await message.answer(
            "Номер чата должен быть из списка, попробуйте ещё раз")
        return
    chat_id = chats_list[chat_number - 1]["id"]
    if chat_id == 0:
        await message.answer("Чат не найден, попробуйте другой запрос")
        return
    await state.update_data(chat_id=chat_id)
    client = Client(f"user_{user.telegram_id}",
                    session_string=user.session_string,
                    in_memory=True)
    try:
        await client.connect()
    except ConnectionError:
        await message.answer("Ошибка подключения к Telegram API, попробуйте зарегестрироваться снова командой /register")
        return
    except FloodWait as e:
        await message.answer(f"Подождите {e.x} секунд и попробуйте снова")
        return
    except Exception as e:
        await message.answer(f"Неизвестная ошибка: {e}")
        return
    try:
        await client.disconnect()
    except Exception as e:
        pass
    chat = Chat.get(chat_id=chat_id, user=user)
    await message.answer(
        f"Чат {chat.title} найден, задайте вопрос", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ExploreChat.explore_chat)


@explore_router.message(ExploreChat.explore_chat)
async def explore_chat(message: Message, state: FSMContext):
    user: User = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        return
    data = await state.get_data()
    chat_id = data.get("chat_id")
    context = data.get("context", None)
    await message.answer("Анализирую сообщения... Это может занять некоторое время")
    chat = Chat.get_or_none(chat_id=chat_id, user=user)
    if chat is None:
        await message.answer("Чат не найден")
        return
    messages = TelegramMessage.select().where(TelegramMessage.chat == chat)
    messages = messages.order_by(TelegramMessage.datetime)
    msgs = []
    for m in messages:
        msgs.append(Msg(datetime=m.datetime, text=m.text, user=m.username))
    await message.answer("Сообщения получены, начинаю анализ")
    try:
        answer_list = await explain_chat(msgs, context, message.text)
        if len(answer_list) == 1:
            raise ValueError(answer_list[0])
        answer, context = answer_list
    except Exception as e:
        await message.answer(
            "Что-то пошло не так, пожалуйста, попробуйте позже\n"
            f"Error: {e}")
        return
    answer = to_markdown(answer)
    if len(answer) > 4000:
        symbols = 0
        for i in range(0, len(answer), 4000):
            symbols += len(answer[i:i+4000])
            if symbols >= len(answer):
                await message.answer(
                    f"{answer[i:i+4000]}\n\nВы можете ещё раз задать вопрос по этой теме", parse_mode="HTML")
                return
            await message.answer(f"{answer[i:i+4000]}...", parse_mode="HTML")
            await asyncio.wait(3)
    else:
        await message.answer(f"{answer}\n\nВы можете ещё раз задать вопрос по этой теме", parse_mode="HTML")
    await state.update_data(context=context)
