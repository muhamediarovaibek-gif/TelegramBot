from aiogram import Bot, Dispatcher
import asyncio

from config import BOT_TOKEN
from handlers import router
from database import create_database
from scheduler import check_leave_statuses

async def main():
    # Создаем таблицы в базе данных (если их еще нет)
    create_database()

    # Создаем объект бота
    bot = Bot(token=BOT_TOKEN)

    # Создаем Dispatcher
    dp = Dispatcher()

    # Подключаем Router из handlers.py
    dp.include_router(router)

    # Подключаем сообщение при окончании больничного
    asyncio.create_task(
        check_leave_statuses(bot)
    )

    # Сообщение после запуска бота
    print("Бот успешно запущен!")

    # Начинаем получать сообщения от Telegram
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())