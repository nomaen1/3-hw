from aiogram import Dispatcher, Bot, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from pytube import YouTube
from config import token 
import logging
import sqlite3
import time
import os

bot = Bot(token)
dp = Dispatcher(bot, storage=MemoryStorage())
storage = MemoryStorage()
logging.basicConfig(level=logging.INFO)

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

buttons = [
    KeyboardButton('/start'),
    KeyboardButton('/help'),
    KeyboardButton('/video'),
    KeyboardButton('/audio'),
    KeyboardButton('/info'),
    KeyboardButton('Отправить номер', request_contact=True),
    KeyboardButton('Отправить локацию', request_location=True)
]

reply_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(*buttons)

inline_buttons = [
    InlineKeyboardButton('Скачать видео', callback_data='video'),
    InlineKeyboardButton('Скачать аудио', callback_data='audio'),
    InlineKeyboardButton('Получить информацию о видео', callback_data='info')
]

inline_reply_button = InlineKeyboardMarkup().add(*inline_buttons)

@dp.message_handler(commands=['start'])
async def start(message:types.Message):
    cursor = db.cursor()
    cursor.execute(f"SELECT id FROM users WHERE id = {message.chat.id};")
    res = cursor.fetchall()
    if res == []:
        cursor.execute(f"""INSERT INTO users VALUES ('{message.from_user.username}', 
        '{message.from_user.first_name}', '{message.from_user.last_name}',
        {message.chat.id}, '{time.ctime()}');""")
    cursor.connection.commit()
    await message.answer(f"Здраствуйте {message.from_user.full_name}\nЯ помогу скачать видео или аудио с YouTube и по возможности отправлю тебе его!", reply_markup = reply_button)

@dp.message_handler(commands=['stats'])
async def get_stats(message:types.Message):
    if message.from_user.id in [686774951]:
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(id) FROM users;")
        res_count = cursor.fetchall()
        await message.reply(f"Пользователей: {res_count[0][0]}")
    else:
        await message.reply("У вас нет прав")

@dp.message_handler(content_types=types.ContentType.CONTACT)
async def help(message:types.Message):
    print(message.contact.phone_number)

@dp.message_handler(content_types=types.ContentType.LOCATION)
async def get_location(message:types.Message):
    print(message.location)

@dp.message_handler(commands=['help'])
async def help(message:types.Message):
    await message.answer("Вот мои комманды:\n/start - запустить бота\n/video - скачать видео\n/audio скачать аудио\n/info - получить информацию о видео", reply_markup= inline_reply_button)

class DownloadVideo(StatesGroup):
    download = State()

class DownloadAudio(StatesGroup):
    download = State()

class MailingState(StatesGroup):
    mail_text = State()

class InfoState(StatesGroup):
    info = State()

@dp.message_handler(commands = ['info'])
async def get_info(message:types.Message):
    await message.reply("Отправь мне ссылку на видео и я вам отправлю информацию")
    await InfoState.info.set()

@dp.callback_query_handler(lambda c: c.data == 'info')
async def process_callback_info(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Отправьте ссылку на видео и я вам отправлю информацию')
    await InfoState.info.set()

@dp.message_handler(state=InfoState.info)
async def send_info_video(message:types.Message, state:FSMContext):
    try:
        yt = YouTube(message.text)
    except:
        await message.reply("Неправильная ссылка на видео")
        await state.finish()
    await message.answer("Начинаю искать инфу...")
    await message.answer(f"Название: {yt.title}\nАвтор: {yt.author}\nДлина: {yt.length} сек\nПросмотры: {yt.views}\nОписание: {yt.description}")
    await state.finish()

@dp.message_handler(commands=['mailing'])
async def mailing(message:types.Message):
    if message.from_user.id == 686774951:
        await message.reply("Введите текст для рассылки")
        await MailingState.mail_text.set()
    else:
        await message.reply("У вас нет прав")

@dp.message_handler(state=MailingState.mail_text)
async def send_mailing(message:types.Message, state:FSMContext):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users;")
    result = cursor.fetchall()
    for user in result:
        await bot.send_message(user[0], message.text)
    await message.answer("Рассылка закончена")
    await state.finish()

@dp.message_handler(commands=['video'])
async def video(message:types.Message):
    await message.answer("Отправьте ссылку на видео и я вам его скачаю")
    await DownloadVideo.download.set()

@dp.callback_query_handler(lambda c: c.data == 'video')
async def process_callback_video(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Отправьте ссылку на видео и я вам его скачаю')
    await DownloadVideo.download.set()

@dp.message_handler(state=DownloadVideo.download)
async def download_video(message:types.Message, state:FSMContext):
    await message.answer("Начинаю скачивать видео, ожидайте...")
    try:
        yt = YouTube(message.text)
    except:
        await message.reply("Неправильная ссылка на видео")
        await state.finish()
    yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download('video', f'{yt.title}.mp4')
    await message.answer("Видео скачалось, отправляю")
    try:
        with open(f'video/{yt.title}.mp4', 'rb') as send_video:
            await message.answer_video(send_video)
    except:
        await message.answer("Произошла ошибка попробуйте позже")
    await os.remove(f'video/{yt.title}.mp4')
    await state.finish()

@dp.message_handler(commands=['audio'])
async def audio(message:types.Message):
    await message.answer("Отправьте ссылку на видео и я вам отправлю ее mp3 формате")
    await DownloadAudio.download.set()
 
@dp.callback_query_handler(lambda c: c.data == 'audio')
async def process_callback_audio(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Отправьте ссылку на видео и я вам отправлю ее mp3 формате')
    await DownloadAudio.download.set()

@dp.message_handler(state=DownloadAudio.download)
async def download_audio(message:types.Message, state:FSMContext):
    await message.answer("Начинаю скачивать аудио, ожидайте...")
    try:
        yt = YouTube(message.text)
    except:
        await message.reply("Неправильная ссылка на видео")
        await state.finish()
    yt.streams.filter(only_audio=True).first().download('audio', f'{yt.title}.mp3')
    await message.answer("Аудио скачалось, отправляю")
    try:
        with open(f'audio/{yt.title}.mp3', 'rb') as send_audio:
            await message.answer_audio(send_audio)
    except:
        await message.answer("Произошла ошибка попробуйте позже")
    await os.remove(f'video/{yt.title}.mp3')
    await state.finish()

@dp.message_handler()
async def not_found(message:types.Message):
    await message.reply("Я вас не понял, введите /help")

executor.start_polling(dp)