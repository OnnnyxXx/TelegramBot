from aiogram.dispatcher.filters import Text, Command
import requests
import datetime
# from bacrount import keep_alive
import aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from api_config import open_wake_token
from api_config import token_bot
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware

bot = Bot(token_bot)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Словарь для хранения последних сообщений пользователей
last_user_messages = {}


# Функция для создания клавиатуры с кнопкой "Отправить название города снова" и последним сообщением пользователя
def create_city_retry_keyboard(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add()

    # Получаем последнее сообщение пользователя из словаря
    last_message = last_user_messages.get(user_id)

    # Если есть последнее сообщение, добавляем его в клавиатуру
    if last_message:
        keyboard.add(last_message)

    return keyboard


@dp.message_handler(commands=['start'])
async def start_commands(message: types.Message):
    start_buttons = ['Погода⛅️']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)
    await message.answer('Привет! {0.first_name} 👋'.format(message.from_user), reply_markup=keyboard)


@dp.message_handler(Text(equals="Погода⛅️"))
async def get_weather(message: types.Message):
    await message.answer("Введи название города 🌇 для получения погоды:")


@dp.message_handler(lambda message: message.text and not message.text.startswith('/'))
async def process_city(message: types.Message):
    city_name = message.text
    code_to_smile = {
        "Clear": "Ясно ☀️",
        "Clouds": "Облачно ☁️",
        "Rain": "Дождь 🌧",
        "Drizzle": "Дождь 🌧",
        "Thunderstorm": "Гроза ⛈",
        "Snow": "Снег ❄️",
        "Mist": "Туман 🌫"
    }

    try:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={open_wake_token}&units=metric"
        )
        data = response.json()

        if data["cod"] == 200:
            city = data["name"]
            cur_weather = data["main"]["temp"]
            weather_description = data["weather"][0]["main"]

            if weather_description in code_to_smile:
                wd = code_to_smile[weather_description]
            else:
                wd = "Посмотри в окно, не пойму что там за погода!"

            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
            sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
            length_of_the_day = datetime.datetime.fromtimestamp(
                data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(
                data["sys"]["sunrise"])

            # Сохраняем последнее сообщение пользователя
            last_user_messages[message.from_user.id] = city_name

            keyboard = create_city_retry_keyboard(message.from_user.id)

            await message.answer(f"{datetime.datetime.now().strftime('%H:%M %Y-%m-%d')}\n"
                                 f"Погода в городе: {city}\n"
                                 f"{message.from_user.first_name} Погода на улице: {cur_weather}°C {wd}\n"
                                 f"Влажность: {humidity}%\nВетер: {wind} м/с\n"
                                 "-------------------------------------------\n"
                                 f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность "
                                 f"дня: {length_of_the_day}\n"
                                 f"Хорошего дня, {message.from_user.first_name} 😊",
                                 reply_markup=keyboard)
        else:
            await message.answer("Город не найден. Проверь название города и попробуй снова.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при получении погоды: {str(e)}")


# keep_alive()
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)