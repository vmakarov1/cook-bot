from dotenv import load_dotenv
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import requests

# Токены берутся из переменных окружения
load_dotenv("tokens.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPOONACULAR_KEY = os.getenv("SPOONACULAR_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Временное хранилище текущих найденных рецептов для каждого пользователя
user_context = {}


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

    if not recipes:
        await message.answer("😔 Ничего не нашёл. Попробуй добавить другие продукты.")
        return

    # сохраняем список найденных рецептов
    user_context[user_id] = recipes

    kb = InlineKeyboardMarkup()
    for r in recipes:
        kb.add(InlineKeyboardButton(r["title"], callback_data=f"recipe_{r['id']}"))
    kb.add(InlineKeyboardButton("🔍 Поиск заново", callback_data="restart"))

    await message.answer("Вот что удалось найти 👇", reply_markup=kb)


#  Показ конкретного рецепта
@dp.callback_query_handler(lambda c: c.data.startswith("recipe_"))
async def show_recipe(callback: types.CallbackQuery):
    recipe_id = callback.data.split("_")[1]
    details = get_recipe_details(recipe_id)

    # текст рецепта
    text = f"🍽 <b>{details['title']}</b>\n"
    text += f"⏱ Время приготовления: {details.get('readyInMinutes', '—')} мин\n"
    text += f"👥 Порций: {details.get('servings', '—')}\n\n"

    text += "<b>Ингредиенты:</b>\n"
    for ing in details["extendedIngredients"]:
        text += f"• {ing['name']} — {ing['amount']} {ing['unit']}\n"



#  Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp)