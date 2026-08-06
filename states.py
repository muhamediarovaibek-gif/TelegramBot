from aiogram.fsm.state import State, StatesGroup


class VacationState(StatesGroup):

    waiting_for_days = State()