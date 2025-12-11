from dotenv import load_dotenv
import os
import json
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


#  Функции работы с избранным
def load_favorites():
    try:
        with open("users_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_favorites(data):
    with open("users_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

favorites = load_favorites()



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
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⭐ Мои избранные", callback_data="show_favorites"))

    await message.answer(
        "Привет! Я помогу тебе найти рецепты по ингредиентам 😊\n\n"
        "Просто напиши, что у тебя есть. Например:\n"
        "<b>курица лук рис</b>\n\n"
        "Или нажми кнопку:",
        reply_markup=kb,
        parse_mode="HTML"
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

    # кнопки
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))
    kb.add(InlineKeyboardButton("❤️ В избранное", callback_data=f"fav_{recipe_id}"))
    kb.add(InlineKeyboardButton("🔍 Поиск заново", callback_data="restart"))

    # текст рецепта
    text = f"🍽 <b>{details['title']}</b>\n"
    text += f"⏱ Время приготовления: {details.get('readyInMinutes', '—')} мин\n"
    text += f"👥 Порций: {details.get('servings', '—')}\n\n"

    text += "<b>Ингредиенты:</b>\n"
    for ing in details["extendedIngredients"]:
        text += f"• {ing['name']} — {ing['amount']} {ing['unit']}\n"

    text += "\n<b>Шаги приготовления:</b>\n"
    if details.get("analyzedInstructions"):
        for step in details["analyzedInstructions"][0]["steps"]:
            text += f"{step['number']}. {step['step']}\n"
    else:
        text += "Нет шага приготовления.\n"
    
    # фото + текст
    await callback.message.answer_photo(
        photo=details["image"],
        caption=text,
        reply_markup=kb,
        parse_mode="HTML"
    )

    await callback.answer()


#  Кнопка "Назад"
@dp.callback_query_handler(lambda c: c.data == "back")
async def go_back(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    recipes = user_context.get(user_id)

    if not recipes:
        await callback.message.answer("История пуста 😕")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup()
    for r in recipes:
        kb.add(InlineKeyboardButton(r["title"], callback_data=f"recipe_{r['id']}"))
    kb.add(InlineKeyboardButton("🔍 Поиск заново", callback_data="restart"))

    await callback.message.answer("Выбери рецепт 👇", reply_markup=kb)
    await callback.answer()


#  Кнопка "Поиск заново"
@dp.callback_query_handler(lambda c: c.data == "restart")
async def restart(callback: types.CallbackQuery):
    await callback.message.answer("Введите новые ингредиенты:")
    await callback.answer()


# Добавление в избранное
@dp.callback_query_handler(lambda c: c.data.startswith("fav_"))
async def add_favorite(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    recipe_id = callback.data.split("_")[1]

    if user_id not in favorites:
        favorites[user_id] = []

    if recipe_id in favorites[user_id]:
        await callback.answer("Уже в избранном ❤️")
        return

    favorites[user_id].append(recipe_id)
    save_favorites(favorites)

    await callback.answer("Добавлено в избранное ❤️")


#  Показ избранных рецептов
@dp.callback_query_handler(lambda c: c.data == "show_favorites")
async def show_favorites(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    fav_list = favorites.get(user_id, [])

    if not fav_list:
        await callback.message.answer("У вас нет избранных рецептов ⭐")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup()

    for recipe_id in fav_list:
        details = get_recipe_details(recipe_id)
        kb.add(InlineKeyboardButton(details["title"], callback_data=f"recipe_{recipe_id}"))

    kb.add(InlineKeyboardButton("🔍 Поиск заново", callback_data="restart"))

    await callback.message.answer("⭐ Ваши избранные рецепты:", reply_markup=kb)
    await callback.answer()


#  Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp)