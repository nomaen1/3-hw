from aiogram import Bot, Dispatcher, executor, types
from config import token
import sqlite3
import time

bot = Bot(token)
dp = Dispatcher(bot)

db = sqlite3.connect('users.db')
cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username VARCHAR(255),
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        id INTEGER,
        created VARCHAR(255)
    );  
""")
cursor.connection.commit()

@dp.message_handler(commands=['start', 'go', 's'])
async def start(message:types.Message):
    cursor = db.cursor()
    cursor.execute(f"SELECT id FROM users WHERE id = {message.chat.id};")
    res = cursor.fetchall()
    if res == []:
        cursor.execute(f"""INSERT INTO users VALUES ('{message.from_user.username}', 
        '{message.from_user.first_name}', '{message.from_user.last_name}',
        {message.chat.id}, '{time.ctime()}');""")
    cursor.connection.commit()
    await message.answer(f"Привет {message.from_user.full_name}")

@dp.message_handler(commands=['help'])
async def help(message:types.Message):
    await message.answer("Вот мои комманды\n/start - запустить бота")

@dp.message_handler(text=["Привет"])
async def hello(message:types.Message):
    await message.reply("Привет")

@dp.message_handler(commands=['test'])
async def test(message:types.Message):
    await message.answer_photo('https://static.tildacdn.com/tild3863-3635-4138-b133-613431396662/230124-237_2.jpg')
    with open('python.png', 'rb') as photo:
        await message.answer_photo(photo)
    await message.answer_location(40.51932163776069, 72.80304539293628)
    await message.answer_dice()

@dp.message_handler()
async def not_found(message:types.Message):
    await message.reply("Я вас не понял, введите /help")

executor.start_polling(dp)