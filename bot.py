from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Токены берутся из переменных окружения
load_dotenv("tokens.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

#  Команда /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "Привет! Я помогу тебе найти рецепты по ингредиентам 😊"
    )

#  Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp)