from aiogram import Router
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from tgbot.misc.states import Registration
from tgbot.models.models import User, ActivationCode
from pyrogram.client import Client
from tgbot.config import load_config
from pyrogram.errors import RPCError, SessionPasswordNeeded, PasswordHashInvalid
from aiogram import types
from tgbot.keyboards.inline import get_code_keyboard
from aiogram.filters import Command
import asyncio
from tgbot.handlers.pyrogram_handlers import get_message_handler
from tgbot.handlers.start import start


registration_router = Router()


async def login(
    phone: str,
    code: str = "",
    phone_hash: str = "",
    password: str = "",
    client: Client = None
) -> dict:
    config = load_config()
    app = client
    if client is None:
        app = Client("sample",
                     api_id=config.pyrogram.api_id,
                     api_hash=config.pyrogram.api_hash,
                     in_memory=True,
                     device_model="ChatsExplorer")
        await app.connect()
    try:
        # await app.connect()
        if not code:
            code_result = await app.send_code(phone)
            to_return = {
                "status": "CODE",
                "phone_code_hash": code_result.phone_code_hash,
                "client": app
            }

        if code and phone_hash:
            await app.sign_in(phone_number=phone, phone_code_hash=phone_hash,
                              phone_code=code)
            to_return = {"status": "OK",
                         "client": app}
    except SessionPasswordNeeded:
        if password:
            try:
                # app.password = password
                await app.check_password(password)
                await app.sign_in(phone, phone_hash, code)
                to_return = {"status": "OK",
                             "client": app}
            except PasswordHashInvalid:
                to_return = {
                    "status": "INVALID_PASSWORD",
                    "client": app
                }
        else:
            to_return = {
                "status": "PASSWORD",
                "client": app
            }
    except RPCError as e:
        to_return = {"status": "ERROR", "message": e}
        await app.disconnect()
    finally:
        # await app.disconnect()
        pass
    return to_return


@registration_router.message(Command("register"))
async def registration(message: Message, state: FSMContext):
    user = User.get_or_none(telegram_id=message.from_user.id)
    if user is not None:
        await activation_key(message, state)
        return
    await message.answer(
        "Привет, введи ключ активации, который тебе выдал администратор")
    await state.set_state(Registration.waiting_for_activation_key)


@registration_router.message(
    Registration.waiting_for_activation_key)
async def activation_key(message: Message, state: FSMContext):
    user = User.get_or_none(telegram_id=message.from_user.id)
    if user is None:
        activation_key = message.text
        code = ActivationCode.get_or_none(code=activation_key,
                                          is_used=False)
        if code is None:
            await message.answer(
                "Ключ активации не найден или уже был использован")
            return
        await state.update_data(activation_code=code)
    phone_keyboard = ReplyKeyboardMarkup(resize_keyboard=True,
                                         one_time_keyboard=True,
                                         keyboard=[
                                             [
                                                 KeyboardButton(
                                                     text="Отправить номер телефона",
                                                     request_contact=True)
                                             ]
                                         ])
    await message.answer(
        "Отлично, теперь отправь свой номер телефона с помощью кнопки",
        reply_markup=phone_keyboard)
    await state.set_state(Registration.waiting_for_phone_number)


@registration_router.message(
    Registration.waiting_for_phone_number)
async def phone_number(message: Message, state: FSMContext):
    contact = message.contact
    if contact is None:
        await message.answer(
            "Пожалуйста, отправь номер телефона с помощью кнопки")
        return
    phone_number = contact.phone_number
    if contact.user_id != message.from_user.id:
        await message.answer(
            "В целях безопасности, вы не можете использовать не свой номер")
        return
    await state.update_data(phone_number=phone_number)
    config = load_config()
    await message.answer(
        "Обрабатываем ваш номер телефона, подождите")
    login_result = await login(phone_number)
    if login_result["status"] == "CODE":
        await message.answer(
            "Telegram отправил код подтверждение, введи его. Твои данные полностью защищены и не видны разработчикам\n\nКод: ",
            reply_markup=get_code_keyboard().as_markup())
        await state.set_state(Registration.waiting_for_phone_code)
        await state.update_data(phone_hash=login_result["phone_code_hash"])
        await state.update_data(client=login_result["client"])
    else:
        await state.clear()
        await message.answer(
            "Что то пошло не так, попробуйте ещё раз: /start")


async def run_pyrogram_client(client: Client):
    await client.start()
    me = await client.get_me()
    print(f"Client {me.id} has been started")


async def create_user(client: Client, activation_code: ActivationCode,
                      phone_number: str):
    try:
        me = await client.get_me()
        user_id = me.id
        session_string = await client.export_session_string()
        await client.disconnect()
        user = User.get_or_none(telegram_id=user_id)
        if user is not None:
            user.session_string = session_string
            user.save()
            return user
        activation_code.is_used = True
        activation_code.save()
        user = User.create(
            telegram_id=user_id,
            phone=phone_number,
            session_string=session_string
        )
        handler = get_message_handler()
        client = Client(
                    name=f"user_{user.telegram_id}",
                    session_string=user.session_string,
                    in_memory=True,
                    device_model="ChatsExplorer"
                )
        client.add_handler(handler)

        loop = asyncio.get_event_loop()
        task = loop.create_task(run_pyrogram_client(client))
        await task
    except RPCError as e:
        print(e)
        return None


@registration_router.callback_query(
    lambda c: c.data.isdigit(),
    Registration.waiting_for_phone_code)
async def process_callback_digit(
        callback_query: types.CallbackQuery,
        state: FSMContext):
    # Добавление цифры к коду
    data = await state.get_data()
    code = data.get("phone_code", "")
    code += callback_query.data
    text = f"Telegram отправил код подтверждение, введи его. Твои данные полностью защищены и не видны разработчикам\n\nКод: {code}"
    await state.update_data(phone_code=code)
    if len(code) == 5:
        await callback_query.message.edit_text(text="Подождите, идет проверка кода")
        phone_number = data.get("phone_number")
        phone_hash = data.get("phone_hash")
        client = data.get("client")
        login_result = await login(phone_number,
                                   code,
                                   phone_hash,
                                   client=client)
        if login_result["status"] == "OK":
            await create_user(client,
                              data.get("activation_code"),
                              phone_number)
            await callback_query.answer("Успешное подключение к аккаунту",
                                        show_alert=True)
            await state.clear()
            await start(callback_query.message, state)
            return
        elif login_result["status"] == "PASSWORD":
            text = "Введите пароль от своего аккаунта"
            await callback_query.message.answer(text)
            await state.update_data(client=login_result["client"])
            await state.set_state(Registration.waiting_for_password)
            return
        await callback_query.message.answer(
            "Что то пошло не так, попробуйте ещё раз: /start")
        return

    await callback_query.message.edit_text(
        text=text,
        reply_markup=get_code_keyboard().as_markup())
    await callback_query.answer()


@registration_router.callback_query(
    lambda c: c.data == "delete",
    Registration.waiting_for_phone_code)
async def process_callback_delete(
        callback_query: types.CallbackQuery,
        state: FSMContext):
    # Удаление последней цифры кода
    data = await state.get_data()
    code = data.get("phone_code", "")
    code = code[:-1]
    text = f"Telegram отправил код подтверждение, введи его. Твои данные полностью защищены и не видны разработчикам\n\nКод: {code}"
    await state.update_data(phone_code=code)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=get_code_keyboard().as_markup())
    await callback_query.answer()


@registration_router.message(
    Registration.waiting_for_password)
async def password(message: Message, state: FSMContext):
    password = message.text
    await state.update_data(password=password)
    data = await state.get_data()
    phone_number = data.get("phone_number")
    phone_code = data.get("phone_code")
    phone_hash = data.get("phone_hash")
    client = data.get("client")
    await state.clear()
    login_result = await login(phone_number,
                               phone_code,
                               phone_hash,
                               password,
                               client)
    if login_result["status"] == "OK":
        client = data.get("client")
        await create_user(client,
                          data.get("activation_code"),
                          phone_number)
        await message.answer("Успешное подключение к аккаунту")
        await state.clear()
        await start(message, state)
        return
    if login_result["status"] == "INVALID_PASSWORD":
        await message.answer("Неверный пароль, попробуйте ещё раз")
        return
    await message.answer(
        "Что то пошло не так, попробуйте ещё раз: /start")
