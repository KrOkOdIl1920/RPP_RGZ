from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    waiting_for_name = State()


class AddOperation(StatesGroup):
    waiting_for_type = State()
    waiting_for_amount = State()
    waiting_for_date = State()
