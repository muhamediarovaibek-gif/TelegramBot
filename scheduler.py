import asyncio

from database import (
    get_sick_leaves_ending_tomorrow,
    mark_leave_notification_sent
)

# Сообщение перед окончанием больничного
from keyboards import extend_sick_leave_keyboard

async def check_leave_statuses(bot):

    while True:

        employees = get_sick_leaves_ending_tomorrow()

        for telegram_id, full_name, employee_id in employees:

            await bot.send_message(
                telegram_id,
                "🏥 Ваш больничный заканчивается завтра.\n\n"
                "Продлить его?",
                reply_markup=extend_sick_leave_keyboard()
            )

            mark_leave_notification_sent(employee_id)

        await asyncio.sleep(3600)