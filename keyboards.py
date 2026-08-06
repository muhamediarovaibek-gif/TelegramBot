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
    [KeyboardButton(text="🟢 Пришел")],
    [KeyboardButton(text="🔴 Ушел")],
    [KeyboardButton(text="📊 Моя статистика")],
    [KeyboardButton(text="🏥 Больничный")],
    [KeyboardButton(text="🏖 Отпуск")],
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