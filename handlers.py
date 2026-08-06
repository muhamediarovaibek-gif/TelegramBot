from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import VacationState
from aiogram.types import CallbackQuery

from config import ADMIN_IDS

from keyboards import (
    employee_keyboard,
    admin_keyboard
)

from database import (
    add_employee,
    get_employee_id,
    check_in,
    check_out,
    has_checked_out,
    create_leave,
    get_active_sick_leave,
    get_today_employee_status,
    extend_leave,
    get_total_employees,
    get_today_attendance,
    get_current_leaves,
    get_absent_employees
)

from utils import *

from constants import *

router = Router()


# Команда /start
@router.message(Command("start"))
async def start(message: Message):

    add_employee(
        message.from_user.id,
        message.from_user.full_name
    )

    telegram_id = message.from_user.id


    common_text = (
        f"👋 Добро пожаловать, {message.from_user.full_name}!\n\n"
        "Это бот для учета рабочего времени сотрудников.\n"
        "Вы можете пользоваться кнопками или командами.\n\n"
        "📌 Команды:\n"
        "/checkin — отметить приход\n"
        "/checkout — отметить уход\n"
        "/sick — отметить как на больничном\n"
        "/vacation — отметить как на отпуске\n"
        "/stats — посмотреть свою статистику\n"
        "/help — открыть справку\n"
    )

    if telegram_id in ADMIN_IDS:
        text = common_text + "/report — открыть отчет по сотрудникам\n\nЕсли возникнут вопросы, обратитесь к администратору."
        keyboard = admin_keyboard
    else:
        text = common_text + "\nЕсли возникнут вопросы, обратитесь к администратору."
        keyboard = employee_keyboard

    
    await message.answer(
        text,
        reply_markup=keyboard
    )


# Команда "Пришел"
@router.message(Command("checkin"))
@router.message(F.text == "🟢 Пришел")
async def employee_check_in(message: Message):

    telegram_id = message.from_user.id

    employee_id = get_employee_id(telegram_id)

    today = get_today()

    current_time = get_current_time()

    employee_status = get_today_employee_status(employee_id)

    if employee_status["status"] == WORK:

        await message.answer(
            "⚠️ Сегодня вы уже отметили приход."
        )
        return

    if employee_status["status"] == SICK:

        await message.answer(
            "🏥 Сейчас у вас действует больничный."
        )
        return

    if employee_status["status"] == VACATION:

        await message.answer(
            "🏖 Сейчас вы находитесь в отпуске."
        )
        return

    check_in(
        employee_id,
        today,
        current_time
    )

    await message.answer(
        f"✅ Приход отмечен.\n"
        f"🕒 Время: {current_time}"
    )


# Команда "Ушел"
@router.message(Command("checkout"))
@router.message(F.text == "🔴 Ушел")
async def employee_check_out(message: Message):

    telegram_id = message.from_user.id

    employee_id = get_employee_id(telegram_id)

    today = get_today()

    current_time = get_current_time()

    employee_status = get_today_employee_status(employee_id)

    if employee_status["status"] == NONE:

        await message.answer(
            "⚠️ Сегодня вы еще не отметили приход."
        )
        return

    if employee_status["status"] == SICK:

        await message.answer(
            "🏥 Сейчас у вас действует больничный."
        )
        return

    if employee_status["status"] == VACATION:

        await message.answer(
            "🏖 Сейчас вы находитесь в отпуске."
        )
        return

    if has_checked_out(employee_id):

        await message.answer(
            "⚠️ Сегодня вы уже отметили уход."
        )
        return

    check_out(
        employee_id,
        today,
        current_time
    )

    await message.answer(
        f"✅ Уход отмечен.\n"
        f"🕒 Время: {current_time}"
    )


# Комадна "Больничный"
@router.message(Command("sick"))
@router.message(F.text == "🏥 Больничный")
async def employee_sick_leave(message: Message):

    telegram_id = message.from_user.id

    employee_id = get_employee_id(telegram_id)

    employee_status = get_today_employee_status(employee_id)

    if employee_status["status"] == WORK:

        await message.answer(
            "⚠️ Сегодня вы уже отметили рабочий день."
        )
        return

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

    end_date = add_days(start_date, SICK_LEAVE_DAYS)

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

    leave = get_active_sick_leave(employee_id)

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
async def employee_vacation(message: Message, state: FSMContext):

    employee_id = get_employee_id(message.from_user.id)

    employee_status = get_today_employee_status(employee_id)

    if employee_status["status"] == WORK:

        await message.answer(
            "⚠️ Сегодня вы уже отметили рабочий день."
        )
        return

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

    await state.set_state(VacationState.waiting_for_days)

    await message.answer(
        "🏖 На сколько дней вы уходите в отпуск?"
    )


# Прием количества дней на отпуск
@router.message(VacationState.waiting_for_days)
async def vacation_days(message: Message, state: FSMContext):

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

    employee_id = get_employee_id(message.from_user.id)

    start_date = get_today()

    end_date = add_days(start_date, days)

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

    stats = build_employee_statistics(employee_id)

    if not stats:
        await message.answer(
            "У вас пока нет отметок."
        )
        return

    status_names = {
        WORK: "💼 Работа",
        SICK: "🏥 Больничный",
        VACATION: "🏖 Отпуск"
    }

    text = "📊 Ваша статистика\n\n"

    for day in stats:

        date = day["date"]
        status = day["status"]
        check_in = day["check_in"]
        check_out = day["check_out"]

        text += (
            f"📅 {date}\n"
            f"📌 Статус: {status_names.get(status, status)}\n"
        )

        if status == WORK:

            text += f"🟢 Приход: {check_in}\n"

            if check_out:
                text += f"🔴 Уход: {check_out}\n"
            else:
                text += "🔴 Уход: —\n"

        text += "\n"

    await message.answer(text)


# Команда "Справка"
@router.message(Command("help"))
@router.message(F.text == "📖 Справка")
async def help_command(message: Message):

    telegram_id = message.from_user.id

    common_text = (
        "Доступные команды:\n\n"

        "/start — открыть главное меню\n"
        "/checkin — отметить приход\n"
        "/checkout — отметить уход\n"
        "/sick — отметить как на больничном\n"
        "/vacation — отметить как на отпуске\n"
        "/stats — посмотреть свою статистику\n"
    )

    if telegram_id in ADMIN_IDS:
        text = "📖 Справка администратора\n\n" + common_text + "/report — отчет по сотрудникам\n/help — открыть справку"
    else:
        text = "📖 Справка\n\n" + common_text + "/help — открыть справку"

    
    await message.answer(
        text,
    )


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

    work = get_today_attendance(today)

    current_leaves = get_current_leaves()

    absent = get_absent_employees(today)

    sick = []
    vacation = []

    for leave in current_leaves:

        full_name = leave[0]
        status = leave[1]
        start_date = leave[2]
        end_date = leave[3]

        if status == SICK:

            sick.append((
                full_name,
                end_date
            ))

        elif status == VACATION:

            vacation.append((
                full_name,
                end_date
            ))

    text = build_admin_report(
        today,
        total,
        work,
        sick,
        vacation,
        absent
    )

    await message.answer(text)



