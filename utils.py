from datetime import date, datetime, timedelta
from database import get_active_employee_leave
from constants import WORK


# Текущая дата
def get_today():
    """
    Возвращает сегодняшнюю дату в формате YYYY-MM-DD.
    Используется для хранения в базе данных.
    """
    return date.today().isoformat()


# Текущее время
def get_current_time():
    """
    Возвращает текущее время в формате HH:MM.
    """
    return datetime.now().strftime("%H:%M")


# Красивое отображение даты
def format_date(date_string):
    """
    Преобразует YYYY-MM-DD -> DD.MM.YYYY
    """

    return datetime.strptime(
        date_string,
        "%Y-%m-%d"
    ).strftime("%d.%m.%Y")


# Добавить дни к дате
def add_days(date_string, days):
    """
    Прибавляет указанное количество дней.
    """

    current_date = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    )

    new_date = current_date + timedelta(days=days)

    return new_date.strftime("%Y-%m-%d")


# Формирует статистику сотрудника
def build_employee_statistics(employee_id):

    leave = get_active_employee_leave(employee_id)

    if leave:

        status, start_date, end_date = leave

        return {
            "status": status,
            "start_date": start_date,
            "end_date": end_date
        }

    return {
        "status": WORK
    }


# Формируем отчет количества
def build_admin_count_report(
    today,
    total,
    work,
    sick,
    vacation
):

    text = (
        f"📊 Отчет за {format_date(today)}\n\n"

        f"👥 Всего сотрудников: {total}\n"
        f"💼 Работают: {len(work)}\n"
        f"🏥 Больничный: {len(sick)}\n"
        f"🏖 Отпуск: {len(vacation)}"
    )

    return text


# Формируем отчет список
def build_admin_list_report(
    work,
    sick,
    vacation
):

    text = "👥 Список сотрудников\n\n"

    text += "💼 Работают:\n"

    if work:

        for full_name in work:
            text += f"• {full_name}\n"

    else:
        text += "Нет сотрудников.\n"

    text += "\n🏥 Больничный:\n"

    if sick:

        for full_name, end_date in sick:

            text += (
                f"• {full_name}\n"
                f"  📅 До: {format_date(end_date)}\n"
            )

    else:
        text += "Нет сотрудников.\n"

    text += "\n🏖 Отпуск:\n"

    if vacation:

        for full_name, end_date in vacation:

            text += (
                f"• {full_name}\n"
                f"  📅 До: {format_date(end_date)}\n"
            )

    else:
        text += "Нет сотрудников."

    return text


# Формирует полный отчет
def build_admin_report(
    today,
    total,
    work,
    sick,
    vacation
):

    text = (
        f"📋 Отчет за {format_date(today)}\n\n"

        f"👥 Всего сотрудников: {total}\n"
        f"💼 Работают: {len(work)}\n"
        f"🏥 Больничный: {len(sick)}\n"
        f"🏖 Отпуск: {len(vacation)}\n\n"
    )

    text += "💼 Работают:\n"

    if work:

        for full_name in work:

            text += (
                f"• {full_name}\n"
            )

    else:
        text += "Нет сотрудников.\n"

    text += "\n🏥 Больничный:\n"

    if sick:

        for full_name, end_date in sick:

            text += (
                f"• {full_name}\n"
                f"  📅 До: {format_date(end_date)}\n"
            )

    else:
        text += "Нет сотрудников.\n"

    text += "\n🏖 Отпуск:\n"

    if vacation:

        for full_name, end_date in vacation:

            text += (
                f"• {full_name}\n"
                f"  📅 До: {format_date(end_date)}\n"
            )

    else:
        text += "Нет сотрудников.\n"

    return text


