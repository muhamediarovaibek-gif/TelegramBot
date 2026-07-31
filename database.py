import sqlite3

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
            status TEXT,
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
            check_in,
            status
        )
        VALUES (?, ?, ?, ?)
    """, (
        employee_id,
        date,
        check_in_time,
        "work"
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


# Отметить больничный
def mark_sick(employee_id, date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO attendance (
            employee_id,
            date,
            status
        )
        VALUES (?, ?, ?)
    """, (
        employee_id,
        date,
        "sick"
    ))

    connection.commit()
    connection.close()


# Отметить отгул
def mark_dayoff(employee_id, date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO attendance (
            employee_id,
            date,
            status
        )
        VALUES (?, ?, ?)
    """, (
        employee_id,
        date,
        "dayoff"
    ))

    connection.commit()
    connection.close()


# Получить статус сотрудника
def get_today_status(employee_id, date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT status
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (
        employee_id,
        date
    ))

    result = cursor.fetchone()

    connection.close()

    if result:
        return result[0]

    return None


# Проверка отметки прихода сотрудника
def has_checked_in(employee_id, date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (employee_id, date))

    attendance = cursor.fetchone()

    connection.close()

    return attendance is not None


# Проверка отметки ухода сотрудника
def has_checked_out(employee_id, date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT check_out
        FROM attendance
        WHERE employee_id = ?
        AND date = ?
    """, (employee_id, date))

    result = cursor.fetchone()

    connection.close()

    if result and result[0] is not None:
        return True

    return False


# Статистика сотрудника
def get_employee_statistics(employee_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            date,
            status,
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


# Список отмеченных сотрудников
def get_today_employees(date):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            employees.full_name,
            attendance.status,
            attendance.check_in,
            attendance.check_out
        FROM attendance
        INNER JOIN employees
        ON attendance.employee_id = employees.id
        WHERE attendance.date = ?
        ORDER BY employees.full_name
    """, (date,))

    employees = cursor.fetchall()

    connection.close()

    return employees


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
