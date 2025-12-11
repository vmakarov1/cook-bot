from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Токены берутся из переменных окружения
load_dotenv("tokens.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)


#  API Spoonacular
def search_recipes(ingredients):
    """поиск рецептов по ингредиентам"""
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "ingredients": ",".join(ingredients),
        "number": 5,
        "ranking": 1,
        "apiKey": SPOONACULAR_KEY
    }
    return requests.get(url, params=params).json()

def get_recipe_details(recipe_id):
    """полные данные о рецепте"""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"includeNutrition": False, "apiKey": SPOONACULAR_KEY}
    return requests.get(url, params=params).json()


#  Команда /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):

    await message.answer(
        "Привет! Я помогу тебе найти рецепты по ингредиентам 😊"
    )


#  Обработка текста с ингредиентами
@dp.message_handler()
async def handle_ingredients(message: types.Message):
    user_id = str(message.from_user.id)
    ingredients = message.text.lower().replace(",", " ").split()

    recipes = search_recipes(ingredients)
    

#  Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp)