import sqlite3
from datetime import date

from constants import (
    WORK,
    SICK,
    NONE
)

DATABASE_NAME = "attendance.db"


# Подключение к базе данных
def get_connection():
    
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    
    return connection


# Создание таблиц базы данных
def create_database():
    
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date TEXT,
            check_in TEXT,
            check_out TEXT,
            FOREIGN KEY(employee_id)
                REFERENCES employees(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            status TEXT,
            start_date TEXT,
            end_date TEXT,
            notification_sent INTEGER DEFAULT 0,
            FOREIGN KEY(employee_id)
                REFERENCES employees(id)
        )
    """)

    connection.commit()
    connection.close()


# Добавление нового сотрудника
def add_employee(telegram_id, full_name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO employees (
            telegram_id,
            full_name
        )
        VALUES (?, ?)
    """, (telegram_id, full_name))

    connection.commit()
    connection.close()


# Возвращение ID сотрудника
def get_employee_id(telegram_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM employees
        WHERE telegram_id = ?
    """, (telegram_id,))

    employee = cursor.fetchone()

    connection.close()

    if employee:
        return employee[0]

    return None


# Отметка прихода сотрудника
def check_in(employee_id, date, check_in_time):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO attendance (
            employee_id,
            date,
            check_in
        )
        VALUES (?, ?, ?)
    """, (
        employee_id,
        date,
        check_in_time
    ))

    connection.commit()
    connection.close()


# Отметка ухода сотрудника
def check_out(employee_id, date, check_out_time):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE attendance
        SET check_out = ?
        WHERE employee_id = ?
        AND date = ?
    """, (check_out_time, employee_id, date))

    connection.commit()
    connection.close()


# Проверка отметки ухода сотрудника
def has_checked_out(employee_id):

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT check_out
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (
        employee_id,
        today
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return False

    return result[0] is not None


# Отметка больничного и отпуска
def create_leave(employee_id, status, start_date, end_date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO leave_status (
            employee_id,
            status,
            start_date,
            end_date,
            notification_sent
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        employee_id,
        status,
        start_date,
        end_date,
        0
    ))

    connection.commit()
    connection.close()


# Проверка записей присутствующих сотрудников
def has_attendance_record(employee_id):

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (
        employee_id,
        today
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


# Получить активный статус отсутствующих сотрудников
def get_active_employee_leave(employee_id):

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            status,
            start_date,
            end_date
        FROM leave_status
        WHERE employee_id = ?
        AND start_date <= ?
        AND end_date >= ?
    """, (
        employee_id,
        today,
        today
    ))

    leave = cursor.fetchone()

    connection.close()

    return leave


# Получить активный больничный сотрудника
def get_active_sick_leave(employee_id):

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            employee_id,
            status,
            start_date,
            end_date,
            notification_sent
        FROM leave_status
        WHERE employee_id = ?
        AND status = ?
        AND end_date >= ?
        LIMIT 1
    """, (
        employee_id,
        SICK,
        today
    ))

    leave = cursor.fetchone()

    connection.close()

    if leave is None:
        return None

    return {
        "id": leave[0],
        "employee_id": leave[1],
        "status": leave[2],
        "start_date": leave[3],
        "end_date": leave[4],
        "notification_sent": leave[5]
    }


# Получить историю отсутствующих сотрудников
def get_employee_leave_history(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            status,
            start_date,
            end_date
        FROM leave_status
        WHERE employee_id = ?
        ORDER BY start_date DESC
    """, (
        employee_id,
    ))

    leaves = cursor.fetchall()

    connection.close()

    return leaves


# Получить статус сотрудника
def get_today_employee_status(employee_id):

    leave = get_active_employee_leave(employee_id)

    if leave:

        return {
            "status": leave[0],
            "start_date": leave[1],
            "end_date": leave[2]
        }

    if has_attendance_record(employee_id):

        return {
            "status": WORK
        }

    return {
        "status": NONE
    }


# Получить последний день больничного
def get_sick_leaves_ending_today():

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            employees.telegram_id,
            employees.full_name,
            leave_status.employee_id
        FROM leave_status

        INNER JOIN employees
            ON leave_status.employee_id = employees.id

        WHERE leave_status.status = ?
        AND leave_status.end_date = ?
        AND leave_status.notification_sent = 0
    """, (
        SICK,
        today
    ))

    employees = cursor.fetchall()

    connection.close()

    return employees


# Продлить больничный
def extend_leave(employee_id, new_end_date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE leave_status
        SET
            end_date = ?,
            notification_sent = 0
        WHERE employee_id = ?
        AND status = ?
    """, (
        new_end_date,
        employee_id,
        SICK
    ))

    connection.commit()
    connection.close()


# Подтверждение отправки уведомления
def mark_leave_notification_sent(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE leave_status
        SET notification_sent = 1
        WHERE employee_id = ?
        AND status = ?
    """, (
        employee_id,
        SICK
    ))

    connection.commit()
    connection.close()


# Получить историю работающих сотрудников
def get_employee_attendance(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            date,
            check_in,
            check_out
        FROM attendance
        WHERE employee_id = ?
        ORDER BY date DESC
    """, (employee_id,))

    statistics = cursor.fetchall()

    connection.close()

    return statistics


# Функции для админа

# Количество отмеченных сотрудников
def get_checked_in_count(date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE date = ?
    """, (date,))

    count = cursor.fetchone()[0]

    connection.close()

    return count


# Количество всех сотрудников
def get_total_employees():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM employees
    """)

    total = cursor.fetchone()[0]

    connection.close()

    return total


# Список работающих сотрудников
def get_today_attendance(date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            employees.full_name,
            attendance.check_in,
            attendance.check_out
        FROM attendance

        INNER JOIN employees
            ON attendance.employee_id = employees.id

        WHERE attendance.date = ?

        ORDER BY employees.full_name
    """, (date,))

    attendance = cursor.fetchall()

    connection.close()

    return attendance


# Список отсутствующих сотрудников
def get_current_leaves():

    today = date.today().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            employees.full_name,
            leave_status.status,
            leave_status.start_date,
            leave_status.end_date

        FROM leave_status

        INNER JOIN employees
            ON leave_status.employee_id = employees.id

        WHERE leave_status.start_date <= ?
        AND leave_status.end_date >= ?

        ORDER BY employees.full_name
    """, (
        today,
        today
    ))

    leaves = cursor.fetchall()

    connection.close()

    return leaves


# Список неотмеченных сотрудников
def get_absent_employees(date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT full_name
        FROM employees
        WHERE id NOT IN (
            SELECT employee_id
            FROM attendance
            WHERE date = ?
        )
        ORDER BY full_name
    """, (date,))

    employees = cursor.fetchall()

    connection.close()

    return employees