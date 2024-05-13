from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_activation_key = State()
    waiting_for_phone_number = State()
    waiting_for_phone_code = State()
    waiting_for_password = State()


class ExploreChat(StatesGroup):
    input_dates = State()
    explore_chat = State()


class SelectChat(StatesGroup):
    input_chat = State()
    confirm_chat = State()
