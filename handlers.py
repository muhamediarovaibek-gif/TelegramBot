from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import VacationState
from aiogram.types import CallbackQuery

from config import ADMIN_IDS

from keyboards import (
    employee_keyboard,
    admin_keyboard,
    admin_panel_keyboard,
    edit_employee_keyboard,
    admin_cancel_keyboard,
    delete_employee_keyboard
)

from database import (
    add_employee,
    get_employee_id,
    create_leave,
    get_active_sick_leave,
    get_employee_status,
    extend_leave,
    get_all_employees,
    get_total_employees,
    get_employee,
    telegram_id_exists,
    update_employee_name,
    update_employee_telegram_id,
    delete_employee
)

from utils import *

from states import (
    EditEmployeeState, 
    DeleteEmployeeState
)

from constants import *

router = Router()


# Команда /start
@router.message(Command("start"))
async def start(message: Message):

    telegram_id = message.from_user.id
    full_name = message.from_user.full_name

    employee_id = get_employee_id(telegram_id)

    if employee_id is None:

        add_employee(
            telegram_id,
            full_name
        )

        common_text = (
            f"👋 Добро пожаловать, {full_name}!\n"
            "Вы зарегистрированы в системе.\n\n"

            "📌 Команды:\n"
            "/sick — оформить больничный\n"
            "/vacation — оформить отпуск\n"
            "/stats — посмотреть статистику\n"
            "/help — открыть справку\n"
        )

        if telegram_id in ADMIN_IDS:

            common_text += (
                "/report — открыть отчет по сотрудникам\n"
                "/admin — открыть админ панель\n\n"
                "Если возникнут вопросы, обратитесь "
                "к администратору."
            )

            keyboard = admin_keyboard

        else:

            common_text += (
                "\nЕсли возникнут вопросы, обратитесь "
                "к администратору."
            )

            keyboard = employee_keyboard

        await message.answer(
            common_text,
            reply_markup=keyboard
        )

        return

    common_text = (
        f"👋 С возвращением, {full_name}!\n\n"

        "📌 Команды:\n"
        "/sick — оформить больничный\n"
        "/vacation — оформить отпуск\n"
        "/stats — посмотреть статистику\n"
        "/help — открыть справку\n"
    )

    if telegram_id in ADMIN_IDS:

        common_text += (
            "/report — открыть отчет по сотрудникам\n"
            "/admin — открыть админ панель\n"
        )

        keyboard = admin_keyboard

    else:

        keyboard = employee_keyboard

    await message.answer(
        common_text,
        reply_markup=keyboard
    )


# Команда "Больничный"
@router.message(Command("sick"))
@router.message(F.text == "🏥 Больничный")
async def employee_sick_leave(message: Message):

    telegram_id = message.from_user.id

    employee_id = get_employee_id(telegram_id)

    if employee_id is None:
        await message.answer(
            "❌ Вы не зарегистрированы в системе."
        )
        return

    employee_status = get_employee_status(employee_id)

    if employee_status["status"] == SICK:
        await message.answer(
            "🏥 У вас уже открыт больничный."
        )
        return

    if employee_status["status"] == VACATION:
        await message.answer(
            "🏖 Сейчас вы находитесь в отпуске."
        )
        return

    start_date = get_today()
    end_date = add_days(
        start_date,
        SICK_LEAVE_DAYS
    )

    create_leave(
        employee_id,
        SICK,
        start_date,
        end_date
    )

    await message.answer(
        "🏥 Больничный оформлен.\n"
        f"📅 До: {format_date(end_date)}"
    )


# Продлить больничный
@router.callback_query(F.data == EXTEND_SICK_CALLBACK)
async def extend_sick_leave(callback: CallbackQuery):

    employee_id = get_employee_id(
        callback.from_user.id
    )

    if employee_id is None:
        await callback.answer(
            "❌ Вы не зарегистрированы в системе.",
            show_alert=True
        )
        return

    leave = get_active_sick_leave(employee_id)

    if leave is None:
        await callback.answer(
            "❌ Активный больничный не найден.",
            show_alert=True
        )
        return

    new_end_date = add_days(
        leave["end_date"],
        SICK_LEAVE_EXTENSION_DAYS
    )

    extend_leave(
        employee_id,
        new_end_date
    )

    await callback.message.edit_text(
        f"✅ Больничный продлен.\n"
        f"📅 До: {format_date(new_end_date)}"
    )

    await callback.answer()


# Не продлевать больничный
@router.callback_query(F.data == CANCEL_SICK_CALLBACK)
async def cancel_sick_leave(callback: CallbackQuery):

    await callback.message.edit_text(
        "🏥 Больничный не был продлен.\n\n"
        "Желаем скорейшего выздоровления!"
    )

    await callback.answer()


# Команда Отпуск
@router.message(Command("vacation"))
@router.message(F.text == "🏖 Отпуск")
async def employee_vacation(
    message: Message,
    state: FSMContext
):

    employee_id = get_employee_id(
        message.from_user.id
    )

    if employee_id is None:
        await message.answer(
            "❌ Вы не зарегистрированы в системе."
        )
        return

    employee_status = get_employee_status(
        employee_id
    )

    if employee_status["status"] == SICK:

        await message.answer(
            "🏥 Сейчас у вас действует больничный."
        )
        return

    if employee_status["status"] == VACATION:

        await message.answer(
            "🏖 Вы уже находитесь в отпуске."
        )
        return

    await state.set_state(
        VacationState.waiting_for_days
    )

    await message.answer(
        "🏖 На сколько дней вы уходите в отпуск?"
    )


# Прием количества дней на отпуск
@router.message(VacationState.waiting_for_days)
async def vacation_days(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "Введите количество дней числом."
        )
        return

    days = int(message.text)

    if days <= 0:

        await message.answer(
            "Количество дней должно быть больше нуля."
        )
        return

    employee_id = get_employee_id(
        message.from_user.id
    )

    if employee_id is None:

        await message.answer(
            "❌ Вы не зарегистрированы в системе."
        )

        await state.clear()

        return

    start_date = get_today()

    end_date = add_days(
        start_date,
        days
    )

    create_leave(
        employee_id,
        VACATION,
        start_date,
        end_date
    )

    await state.clear()

    await message.answer(
        f"🏖 Отпуск оформлен.\n"
        f"📅 До: {format_date(end_date)}"
    )


# Команда "Моя статистика"
@router.message(Command("stats"))
@router.message(F.text == "📊 Моя статистика")
async def statistics(message: Message):

    telegram_id = message.from_user.id

    employee_id = get_employee_id(telegram_id)

    if employee_id is None:
        await message.answer(
            "❌ Вы не зарегистрированы в системе."
        )
        return

    stats = build_employee_statistics(employee_id)

    if not stats:
        await message.answer(
            "У вас пока нет больничных или отпусков."
        )
        return

    status_names = {
        SICK: "🏥 Больничный",
        VACATION: "🏖 Отпуск"
    }

    text = "📊 Ваша статистика\n\n"

    for day in stats:

        date = day["date"]
        status = day["status"]

        text += (
            f"📅 {format_date(date)}\n"
            f"📌 Статус: "
            f"{status_names.get(status, status)}\n\n"
        )

    await message.answer(text)


# Команда "Справка"
@router.message(Command("help"))
@router.message(F.text == "📖 Справка")
async def help_command(message: Message):

    telegram_id = message.from_user.id

    common_text = (
        "Доступные команды:\n\n"

        "/start — открыть главное меню\n"
        "/sick — оформить больничный\n"
        "/vacation — оформить отпуск\n"
        "/stats — посмотреть свою статистику\n"
        "/help — открыть справку\n"
    )

    if telegram_id in ADMIN_IDS:

        text = (
            "📖 Справка администратора\n\n"
            + common_text
            + "\n"
            "/report — открыть отчет по сотрудникам\n"
            "/admin — открыть админ панель"
        )

    else:

        text = (
            "📖 Справка\n\n"
            + common_text
        )

    await message.answer(text)


# Функции для админа

# Команда "Отчет"
@router.message(Command("report"))
@router.message(F.text == "📋 Отчет")
async def report(message: Message):

    telegram_id = message.from_user.id

    if telegram_id not in ADMIN_IDS:
        await message.answer(
            "❌ У вас нет доступа."
        )
        return

    today = get_today()

    total = get_total_employees()

    employees = get_all_employees()

    work = []
    sick = []
    vacation = []

    for employee_id, full_name in employees:

        employee_status = get_employee_status(employee_id)

        status = employee_status["status"]

        if status == WORK:

            work.append(full_name)

        elif status == SICK:

            sick.append((
                full_name,
                employee_status["end_date"]
            ))

        elif status == VACATION:

            vacation.append((
                full_name,
                employee_status["end_date"]
            ))

    text = build_admin_report(
        today,
        total,
        work,
        sick,
        vacation
    )

    await message.answer(text)


# Админ-панель
@router.message(Command("admin"))
@router.message(F.text == "🛠 Админ панель")
async def admin_panel(message: Message):

    telegram_id = message.from_user.id

    if telegram_id not in ADMIN_IDS:
        await message.answer(
            "❌ У вас нет доступа."
        )
        return

    await message.answer(
        "🛠 Админ панель\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard
    )


# Назад из админ-панели
@router.message(F.text == "↩️ Назад")
async def admin_panel_back(message: Message):

    telegram_id = message.from_user.id

    if telegram_id not in ADMIN_IDS:
        return

    await message.answer(
        "🏠 Главное меню",
        reply_markup=admin_keyboard
    )


# Список сотрудников
@router.message(F.text == "📋 Список сотрудников")
async def employee_list(message: Message):

    telegram_id = message.from_user.id

    if telegram_id not in ADMIN_IDS:
        await message.answer(
            "❌ У вас нет доступа."
        )
        return

    employees = get_all_employees()

    if not employees:
        await message.answer(
            "👥 Сотрудников пока нет."
        )
        return

    text = "📋 Список сотрудников\n\n"

    for employee_id, full_name in employees:

        text += (
            f"🆔 ID: {employee_id}\n"
            f"👤 {full_name}\n\n"
        )

    await message.answer(text)


# Отмена действии
@router.message(F.text == "❌ Отмена")
async def cancel_admin_action(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        return

    await state.clear()

    await message.answer(
        "❌ Операция отменена.",
        reply_markup=admin_panel_keyboard
    )


# Изменение сотрудника
@router.message(F.text == "✏️ Изменить сотрудника")
async def edit_employee(message: Message, state: FSMContext):

    telegram_id = message.from_user.id

    if telegram_id not in ADMIN_IDS:
        await message.answer(
            "❌ У вас нет доступа."
        )
        return

    await state.set_state(
        EditEmployeeState.waiting_for_employee_id
    )

    await message.answer(
        "✏️ Изменение сотрудника\n\n"
        "Введите ID сотрудника:",
        reply_markup=admin_cancel_keyboard
    )


# Получение ID сотрудника
@router.message(
        EditEmployeeState.waiting_for_employee_id,
        F.text != "❌ Отмена"
)
async def edit_employee_id(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "❌ ID должен быть числом."
        )
        return

    employee_id = int(message.text)

    employee = get_employee(employee_id)

    if employee is None:

        await message.answer(
            "❌ Сотрудник с таким ID не найден."
        )
        return

    await state.update_data(
        employee_id=employee_id
    )

    await state.set_state(
        EditEmployeeState.waiting_for_field
    )

    await message.answer(
        f"👤 Сотрудник: {employee[2]}\n"
        f"🆔 Telegram ID: {employee[1]}\n\n"
        "Что вы хотите изменить?",
        reply_markup=edit_employee_keyboard
    )


# Изменение ФИО сотрудника
@router.message(
    EditEmployeeState.waiting_for_field,
    F.text == "👤 Изменить имя"
)
async def edit_employee_name(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        EditEmployeeState.waiting_for_full_name
    )

    await message.answer(
        "👤 Введите новое ФИО:",
        reply_markup=admin_cancel_keyboard
    )


# Сохранение ФИО сотрудника
@router.message(EditEmployeeState.waiting_for_full_name,
    F.text != "❌ Отмена"
)
async def save_employee_name(
    message: Message,
    state: FSMContext
):

    full_name = message.text.strip()

    if not full_name:

        await message.answer(
            "❌ ФИО не может быть пустым."
        )
        return

    data = await state.get_data()

    employee_id = data["employee_id"]

    update_employee_name(
        employee_id,
        full_name
    )

    await state.clear()

    await message.answer(
        "✅ ФИО сотрудника успешно изменено.",
        reply_markup=admin_panel_keyboard
    )


# Изменение ID сотрудника
@router.message(
    EditEmployeeState.waiting_for_field,
    F.text == "🆔 Изменить Telegram ID"
)
async def edit_employee_telegram_id(
    message: Message,
    state: FSMContext
):

    await state.set_state(
        EditEmployeeState.waiting_for_telegram_id
    )

    await message.answer(
        "🆔 Введите новый Telegram ID:",
        reply_markup=admin_cancel_keyboard
    )


# Сохранение ID сотрудника
@router.message(EditEmployeeState.waiting_for_telegram_id,
    F.text != "❌ Отмена"
)
async def save_employee_telegram_id(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "❌ Telegram ID должен быть числом."
        )
        return

    new_telegram_id = int(message.text)

    data = await state.get_data()

    employee_id = data["employee_id"]

    if telegram_id_exists(
        new_telegram_id,
        employee_id
    ):

        await message.answer(
            "❌ Этот Telegram ID уже принадлежит "
            "другому сотруднику."
        )
        return

    update_employee_telegram_id(
        employee_id,
        new_telegram_id
    )

    await state.clear()

    await message.answer(
        "✅ Telegram ID сотрудника успешно изменён.",
        reply_markup=admin_panel_keyboard
    )


# Удаление сотрудника
@router.message(F.text == "🗑 Удалить сотрудника")
async def delete_employee_start(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        await message.answer(
            "❌ У вас нет доступа."
        )
        return

    await state.set_state(
        DeleteEmployeeState.waiting_for_employee_id
    )

    await message.answer(
        "🗑 Удаление сотрудника\n\n"
        "Введите ID сотрудника:",
        reply_markup=admin_cancel_keyboard
    )


# Получение ID сотрудника
@router.message(
    DeleteEmployeeState.waiting_for_employee_id,
    F.text != "❌ Отмена"
)
async def delete_employee_id(
    message: Message,
    state: FSMContext
):

    if not message.text.isdigit():

        await message.answer(
            "❌ ID должен быть числом."
        )
        return

    employee_id = int(message.text)

    employee = get_employee(employee_id)

    if employee is None:

        await message.answer(
            "❌ Сотрудник с таким ID не найден."
        )
        return

    await state.update_data(
        employee_id=employee_id
    )

    await state.set_state(
        DeleteEmployeeState.waiting_for_confirmation
    )

    await message.answer(
        "⚠️ Вы действительно хотите удалить сотрудника?\n\n"
        f"👤 {employee[2]}\n"
        f"🆔 Telegram ID: {employee[1]}\n\n"
        "Все его записи о больничных и отпусках "
        "также будут удалены.",
        reply_markup=delete_employee_keyboard
    )


# Подтверждение удаления
@router.message(
    DeleteEmployeeState.waiting_for_confirmation,
    F.text == "✅ Да, удалить"
)
async def delete_employee_confirm(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMIN_IDS:
        await state.clear()
        return

    data = await state.get_data()

    employee_id = data["employee_id"]

    delete_employee(employee_id)

    await state.clear()

    await message.answer(
        "✅ Сотрудник успешно удалён.",
        reply_markup=admin_panel_keyboard
    )





