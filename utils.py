from datetime import date, datetime, timedelta
from database import (
    get_employee_attendance,
    get_employee_leave_history
)
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

    attendance_history = get_employee_attendance(employee_id)

    leave_history = get_employee_leave_history(employee_id)

    statistics = {}

    for date, check_in, check_out in attendance_history:

        statistics[date] = {
            "date": date,
            "status": WORK,
            "check_in": check_in,
            "check_out": check_out
        }

    for status, start_date, end_date in leave_history:

        start = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

        end = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

        current_date = start

        while current_date <= end:

            date_key = current_date.isoformat()

            statistics[date_key] = {
                "date": date_key,
                "status": status,
                "check_in": None,
                "check_out": None
            }

            current_date += timedelta(days=1)

    statistics_list = sorted(
        statistics.values(),
        key=lambda item: item["date"],
        reverse=True
    )

    return statistics_list

# Формирует текст отчета
def build_admin_report(
    today,
    total,
    work,
    sick,
    vacation,
    absent
):

    text = (
        f"📋 Отчет за {format_date(today)}\n\n"

        f"👥 Всего сотрудников: {total}\n"
        f"💼 Работают: {len(work)}\n"
        f"🏥 Больничный: {len(sick)}\n"
        f"🏖 Отпуск: {len(vacation)}\n"
        f"❌ Не отметились: {len(absent)}\n\n"
    )

    text += "💼 Работают:\n"

    if work:

        for full_name, check_in, check_out in work:

            text += (
                f"• {full_name}\n"
                f"  🟢 {check_in}\n"
                f"  🔴 {check_out or '—'}\n\n"
            )

    else:
        text += "Нет сотрудников.\n\n"

    text += "🏥 Больничный:\n"

    if sick:

        for full_name, end_date in sick:

            text += (
                f"• {full_name}\n"
                f"  📅 До: {format_date(end_date)}\n\n"
            )

    else:
        text += "Нет сотрудников.\n\n"

    text += "🏖 Отпуск:\n"

    if vacation:

        for full_name, end_date in vacation:

            text += (
                f"• {full_name}\n"
                f"  📅 До: {format_date(end_date)}\n\n"
            )

    else:
        text += "Нет сотрудников.\n\n"

    text += "❌ Не отметились:\n"

    if absent:

        for employee in absent:

            text += f"• {employee[0]}\n"

    else:
        text += "Нет сотрудников."

    return text