from aiogram.fsm.state import State, StatesGroup

# Состояние для отпуска
class VacationState(StatesGroup):

    waiting_for_days = State()


# Состояние для редактирования сотрудников
class EditEmployeeState(StatesGroup):

    waiting_for_employee_id = State()
    waiting_for_field = State()
    waiting_for_full_name = State()
    waiting_for_telegram_id = State()

    waiting_for_status = State()
    waiting_for_sick_days = State()
    waiting_for_vacation_days = State()


# Состояние для удаления сотрудника
class DeleteEmployeeState(StatesGroup):

    waiting_for_employee_id = State()
    waiting_for_confirmation = State()



