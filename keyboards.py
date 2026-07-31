from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)

employee_buttons = [
    [KeyboardButton(text="🟢 Пришел")],
    [KeyboardButton(text="🔴 Ушел")],
    [KeyboardButton(text="📊 Моя статистика")],
    [KeyboardButton(text="🏥 Больничный")],
    [KeyboardButton(text="🏖 Отгул")],
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
        [KeyboardButton(text="📋 Отчет")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)