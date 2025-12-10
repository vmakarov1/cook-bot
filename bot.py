from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Токены берутся из переменных окружения
load_dotenv("tokens.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


#  Запуск бота
if __name__ == "__main__":
    pass