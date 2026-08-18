import sqlite3
from datetime import date

from constants import (
    WORK,
    SICK,
    NONE
)

DATABASE_NAME = "database.db"


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


# Получить сотрудника
def get_employee(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            telegram_id,
            full_name
        FROM employees
        WHERE id = ?
    """, (employee_id,))

    employee = cursor.fetchone()

    connection.close()

    return employee


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
def get_employee_status(employee_id):

    leave = get_active_employee_leave(employee_id)

    if leave:

        return {
            "status": leave[0],
            "start_date": leave[1],
            "end_date": leave[2]
        }

    return {
        "status": WORK
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


# Функции для админа

# Получить всех сотрудников
def get_all_employees():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            full_name
        FROM employees
        ORDER BY full_name
    """)

    employees = cursor.fetchall()

    connection.close()

    return employees


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


# Проверка ID сотрудника
def telegram_id_exists(telegram_id, employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM employees
        WHERE telegram_id = ?
        AND id != ?
    """, (
        telegram_id,
        employee_id
    ))

    employee = cursor.fetchone()

    connection.close()

    return employee is not None


# Изменить ФИО сотрудника
def update_employee_name(employee_id, full_name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE employees
        SET full_name = ?
        WHERE id = ?
    """, (
        full_name,
        employee_id
    ))

    connection.commit()
    connection.close()


# Изменить ID сотрудника
def update_employee_telegram_id(employee_id, telegram_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE employees
        SET telegram_id = ?
        WHERE id = ?
    """, (
        telegram_id,
        employee_id
    ))

    connection.commit()
    connection.close()


# Удалить сотрудника
def delete_employee(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    # Сначала удаляем связанные больничные и отпуска
    cursor.execute("""
        DELETE FROM leave_status
        WHERE employee_id = ?
    """, (employee_id,))

    # Затем удаляем самого сотрудника
    cursor.execute("""
        DELETE FROM employees
        WHERE id = ?
    """, (employee_id,))

    connection.commit()
    connection.close()