from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

from aiogram.utils.keyboard import InlineKeyboardBuilder

from constants import (
    EXTEND_SICK_CALLBACK,
    CANCEL_SICK_CALLBACK
)

employee_buttons = [
    [KeyboardButton(text="🏥 Больничный")],
    [KeyboardButton(text="🏖 Отпуск")],
    [KeyboardButton(text="📊 Моя статистика")],
    [KeyboardButton(text="📖 Справка")]
]

employee_keyboard = ReplyKeyboardMarkup(
    keyboard=employee_buttons,
    resize_keyboard=True,
    one_time_keyboard=False
)


admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        *employee_buttons,
        [KeyboardButton(text="📋 Отчет")],
        [KeyboardButton(text="🛠 Админ панель")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


admin_panel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Список сотрудников")],
        [KeyboardButton(text="✏️ Изменить сотрудника")],
        [KeyboardButton(text="🗑 Удалить сотрудника")],
        [KeyboardButton(text="↩️ Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


edit_employee_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Изменить имя")],
        [KeyboardButton(text="🆔 Изменить Telegram ID")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


admin_cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


delete_employee_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Да, удалить")],
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


def extend_sick_leave_keyboard():

    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Продлить",
        callback_data=EXTEND_SICK_CALLBACK
    )

    builder.button(
        text="❌ Не продлевать",
        callback_data=CANCEL_SICK_CALLBACK
    )

    builder.adjust(2)

    return builder.as_markup()