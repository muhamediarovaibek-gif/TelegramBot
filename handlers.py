from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

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
    mark_sick,
    mark_dayoff,
    get_today_status,
    has_checked_out,
    get_employee_statistics,
    get_checked_in_count,
    get_total_employees,
    get_today_employees,
    get_absent_employees,
)

from datetime import datetime

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
        "/dayoff — отметить как на отгуле\n"
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


# Проверка статуса сотрудника
async def check_today_status(message: Message, employee_id: int, today: str):

    status = get_today_status(employee_id, today)

    if status is None:
        return True

    messages = {
        "work": "⚠️ Сегодня вы уже отметили приход.",
        "sick": "🏥 Сегодня у вас уже отмечен больничный.",
        "dayoff": "🏖 Сегодня у вас уже отмечен отгул."
    }

    await message.answer(
        messages.get(status, "⚠️ Сегодня уже есть отметка.")
    )

    return False


# Команда "Пришел"
@router.message(Command("checkin"))
@router.message(F.text == "🟢 Пришел")
async def employee_check_in(message: Message):

    telegram_id = message.from_user.id

    employee_id = get_employee_id(telegram_id)

    today = datetime.now().strftime("%d.%m.%Y")
    current_time = datetime.now().strftime("%H:%M")

    if not await check_today_status(message, employee_id, today):
        return

    check_in(employee_id, today, current_time)

    await message.answer(
        f"✅ Приход отмечен в {current_time}"
    )


# Команда "Ушел"
@router.message(Command("checkout"))
@router.message(F.text == "🔴 Ушел")
async def employee_check_out(message: Message):

    telegram_id = message.from_user.id
    employee_id = get_employee_id(telegram_id)

    today = datetime.now().strftime("%d.%m.%Y")
    current_time = datetime.now().strftime("%H:%M")

    status = get_today_status(employee_id, today)

    if status is None:
        await message.answer(
            "⚠️ Сначала отметьте приход."
        )
        return

    if status == "sick":
        await message.answer(
            "🏥 Сегодня у вас отмечен больничный."
        )
        return

    if status == "dayoff":
        await message.answer(
            "🏖 Сегодня у вас отмечен отгул."
        )
        return

    if has_checked_out(employee_id, today):
        await message.answer(
            "⚠️ Вы уже отметили уход сегодня."
        )
        return

    check_out(employee_id, today, current_time)

    await message.answer(
        f"👋 Уход отмечен в {current_time}"
    )


# Комадна "Больничный"
@router.message(Command("sick"))
@router.message(F.text == "🏥 Больничный")
async def sick_leave(message: Message):

    telegram_id = message.from_user.id
    employee_id = get_employee_id(telegram_id)

    today = datetime.now().strftime("%d.%m.%Y")

    if not await check_today_status(message, employee_id, today):
        return

    mark_sick(employee_id, today)

    await message.answer(
        "🏥 Больничный успешно отмечен."
    )


# Команда Отгул
@router.message(Command("dayoff"))
@router.message(F.text == "🏖 Отгул")
async def day_off(message: Message):

    telegram_id = message.from_user.id
    employee_id = get_employee_id(telegram_id)

    today = datetime.now().strftime("%d.%m.%Y")

    if not await check_today_status(message, employee_id, today):
        return

    mark_dayoff(employee_id, today)

    await message.answer(
        "🏖 Отгул успешно отмечен."
    )


# Команда "Моя статистика"
@router.message(Command("stats"))
@router.message(F.text == "📊 Моя статистика")
async def statistics(message: Message):

    telegram_id = message.from_user.id
    employee_id = get_employee_id(telegram_id)

    stats = get_employee_statistics(employee_id)

    if not stats:
        await message.answer(
            "У вас пока нет отметок."
        )
        return

    status_names = {
        "work": "💼 Работа",
        "sick": "🏥 Больничный",
        "dayoff": "🏖 Отгул"
    }

    text = "📊 Ваша статистика\n\n"

    for day in stats:

        date = day[0]
        status = day[1]
        check_in = day[2]
        check_out = day[3]

        text += (
            f"📅 {date}\n"
            f"📌 Статус: {status_names.get(status, status)}\n"
        )

        if status == "work":

            text += (
                f"🟢 Приход: {check_in}\n"
            )

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
        "/dayoff — отметить как на отгуле\n"
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

    today = datetime.now().strftime("%d.%m.%Y")

    total = get_total_employees()

    today_employees = get_today_employees(today)

    absent = get_absent_employees(today)

    work = []
    sick = []
    dayoff = []

    for employee in today_employees:

        full_name = employee[0]
        status = employee[1]
        check_in = employee[2]
        check_out = employee[3]

        if status == "work":
            work.append((full_name, check_in, check_out))

        elif status == "sick":
            sick.append(full_name)

        elif status == "dayoff":
            dayoff.append(full_name)

    text = (
        f"📋 Отчет за {today}\n\n"

        f"👥 Всего сотрудников: {total}\n"
        f"💼 Работают: {len(work)}\n"
        f"🏥 Больничный: {len(sick)}\n"
        f"🏖 Отгул: {len(dayoff)}\n"
        f"❌ Не отметились: {len(absent)}\n\n"
    )

    text += "💼 Работают:\n"

    if work:

        for employee in work:

            text += (
                f"• {employee[0]}\n"
                f"  🟢 {employee[1]}\n"
                f"  🔴 {employee[2] or '—'}\n\n"
            )

    else:
        text += "Нет сотрудников.\n\n"

    text += "🏥 Больничный:\n"

    if sick:

        for employee in sick:
            text += f"• {employee}\n"

    else:
        text += "Нет сотрудников."

    text += "\n\n🏖 Отгул:\n"

    if dayoff:

        for employee in dayoff:
            text += f"• {employee}\n"

    else:
        text += "Нет сотрудников."

    text += "\n\n❌ Не отметились:\n"

    if absent:

        for employee in absent:
            text += f"• {employee[0]}\n"

    else:
        text += "Нет сотрудников."

    await message.answer(text)



