import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from groq import Groq
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://USER:PASS@cluster.mongodb.net/zukko_db")

MINI_APP_URL = "https://shoxruz.github.io/"
ADMIN_USERNAME = "shoxruz_cy"

CARD_NUMBER = "9860606761428865"
CARD_OWNER = "Matkarimov Shoxruzbek"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

groq_client = Groq(api_key=GROQ_API_KEY)
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["zukko_english"]
users_col = db["users"]

# Tugmalar ro'yxati (Admin bilan aloqa tugmasi qo'shildi)
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Mini App'ni Ochish", web_app=WebAppInfo(url=MINI_APP_URL))],
        [KeyboardButton(text="📝 Ota-onani Ulash"), KeyboardButton(text="⚡ Premium 2X XP")],
        [KeyboardButton(text="📊 Mening Profilim"), KeyboardButton(text="🤖 AI Ustoz Chat")],
        [KeyboardButton(text="👨‍💻 Admin bilan aloqa")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_data = users_col.find_one({"user_id": user_id})
    
    if not user_data:
        users_col.insert_one({
            "user_id": user_id,
            "name": message.from_user.first_name,
            "xp": 0,
            "parent_id": None,
            "is_premium": False
        })

    welcome_text = (
        f"Salom <b>{message.from_user.first_name}</b>! 👋\n\n"
        f"Men <b>Zukko English AI</b> ustozingizman.\n"
        f"Mini App orqali darslar va o'yinlarni topshirishingiz mumkin."
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_keyboard)

# Admin bilan aloqa tugmasi
@dp.message(F.text == "👨‍💻 Admin bilan aloqa")
async def contact_admin(message: types.Message):
    inline_admin = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Adminga yozish (@shoxruz_cy)", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    await message.answer(
        "🛠 <b>Savol yoki muammo yuzaga kelsa adminga bog'laning:</b>",
        parse_mode="HTML",
        reply_markup=inline_admin
    )

@dp.message(F.text == "📝 Ota-onani Ulash")
async def link_parent_request(message: types.Message):
    await message.answer(
        "👨‍👩‍👧 Ota-onangizning Telegram <b>ID raqamini</b> yozib yuboring:\n\n"
        "<i>Eslatma: Ota-onangiz avval ushbu botga kirib /start bosgan bo'lishi shart!</i>",
        parse_mode="HTML"
    )

@dp.message(F.text.isdigit())
async def process_parent_id(message: types.Message):
    parent_id = int(message.text)
    user_id = message.from_user.id

    parent_data = users_col.find_one({"user_id": parent_id})

    if not parent_data:
        await message.answer(
            "❌ <b>Xatolik!</b> Ushbu ID ega bo'lgan foydalanuvchi botga /start bosmagan.\n"
            "Avval ota-onangiz botga kirib /start tugmasini bosishlari kerak.",
            parse_mode="HTML"
        )
        return

    users_col.update_one({"user_id": user_id}, {"$set": {"parent_id": parent_id}})
    await message.answer("✅ Ota-ona hisobi muvaffaqiyatli ulandi!")
    
    try:
        await bot.send_message(
            parent_id, 
            f"🔔 Siz <b>{message.from_user.first_name}</b> ning hisobiga ota-ona sifatida ulandingiz!",
            parse_mode="HTML"
        )
    except Exception:
        pass

@dp.message(F.text == "🤖 AI Ustoz Chat")
async def ai_chat_prompt(message: types.Message):
    await message.answer("Ingliz tili bo'yicha savolingizni yozing, AI Ustoz javob beradi:")

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_ai_response(message: types.Message):
    if message.text in ["🚀 Mini App'ni Ochish", "📝 Ota-onani Ulash", "⚡ Premium 2X XP", "📊 Mening Profilim", "👨‍💻 Admin bilan aloqa"]:
        return

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Siz samimiy va yordamchi ingliz tili o'qituvchisisiz. O'zbek tilida qisqa va tushunarli javob bering."},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        await message.answer(completion.choices[0].message.content)
    except Exception:
        await message.answer("Hozircha AI serveriga ulanishda biroz uzilish bo'ldi. Qaytadan urinib ko'ring.")

@dp.message(F.text == "⚡ Premium 2X XP")
async def premium_info(message: types.Message):
    pay_text = (
        f"⚡ <b>Zukko English Premium (2X XP)</b>\n\n"
        f"💳 <b>To'lov uchun karta:</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"👤 <b>Ega:</b> {CARD_OWNER}\n\n"
        f"To'lov qilgach, chekni rasm shaklida botga yuboring!"
    )
    await message.answer(pay_text, parse_mode="HTML")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

