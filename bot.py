import os
import json
import hmac
import hashlib
import logging
import asyncio
import psycopg2
from urllib.parse import parse_qsl
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
DATABASE_URL = os.getenv("DATABASE_URL")

MINI_APP_URL = "https://shoxruz.github.io/"
ADMIN_USERNAME = "shoxruz_cy"

# XAVFSIZLIK: karta ma'lumotlarini kodga yozmang!
# Render -> Settings -> Environment bo'limiga CARD_NUMBER va CARD_OWNER qo'shing.
CARD_NUMBER = os.getenv("CARD_NUMBER", "0000000000000000")
CARD_OWNER = os.getenv("CARD_OWNER", "Ism Familiya")

# Groq'da llama-3.3-70b-versatile modeli decommission qilingan (404 xatosi shundan).
# Yangi model nomini environment orqali ham o'zgartirish mumkin.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
groq_client = Groq(api_key=GROQ_API_KEY)


def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zukko_users (
            user_id BIGINT PRIMARY KEY,
            name TEXT,
            xp INT DEFAULT 0,
            parent_id BIGINT,
            is_premium BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()


init_db()

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
    name = message.from_user.first_name

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM zukko_users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO zukko_users (user_id, name, xp, parent_id, is_premium) VALUES (%s, %s, 0, NULL, FALSE)",
            (user_id, name)
        )
        conn.commit()

    cursor.close()
    conn.close()

    welcome_text = (
        f"Salom <b>{name}</b>! 👋\n\n"
        f"Men <b>Zukko English AI</b> ustozingizman.\n"
        f"Mini App orqali darslar va o'yinlarni topshirishingiz mumkin."
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=main_keyboard)


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

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM zukko_users WHERE user_id = %s", (parent_id,))
    parent_data = cursor.fetchone()

    if not parent_data:
        cursor.close()
        conn.close()
        await message.answer(
            "❌ <b>Xatolik!</b> Ushbu ID ega bo'lgan foydalanuvchi botga /start bosmagan.\n"
            "Avval ota-onangiz botga kirib /start tugmasini bosishlari kerak.",
            parse_mode="HTML"
        )
        return

    cursor.execute("UPDATE zukko_users SET parent_id = %s WHERE user_id = %s", (parent_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()

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


@dp.message(F.text & ~F.text.startswith("/"))
async def handle_ai_response(message: types.Message):
    if message.text in [
        "🚀 Mini App'ni Ochish", "📝 Ota-onani Ulash", "⚡ Premium 2X XP",
        "📊 Mening Profilim", "👨‍💻 Admin bilan aloqa", "🤖 AI Ustoz Chat"
    ]:
        return

    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "Siz samimiy va yordamchi ingliz tili o'qituvchisisiz. O'zbek tilida qisqa va tushunarli javob bering."},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,
            max_tokens=500
        )
        await message.answer(completion.choices[0].message.content)
    except Exception as e:
        logging.error(f"Groq xatosi: {e}")
        await message.answer("Hozircha AI serveriga ulanishda biroz uzilish bo'ldi. Qaytadan urinib ko'ring.")


# --- Mini App API: Telegram WebApp bilan bazani bog'lash ---

def verify_init_data(init_data: str) -> dict | None:
    """
    Telegram WebApp initData'ni bot tokeni bilan tasdiqlaydi.
    Bu bo'lmasa, istalgan odam o'z XP'sini soxta oshirib yuborishi mumkin edi.
    Rasmiy Telegram algoritmi: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user = json.loads(parsed.get("user", "{}"))
        return user
    except Exception as e:
        logging.error(f"initData tekshirishda xato: {e}")
        return None


def cors_response(data: dict, status: int = 200) -> web.Response:
    resp = web.json_response(data, status=status)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


async def handle_options(request):
    return cors_response({})


async def handle_ping(request):
    return web.Response(text="Zukko English Bot ishlayapti ✅")


async def handle_sync(request):
    """
    Mini App shu endpoint'ga initData va (ixtiyoriy) xp_delta yuboradi.
    Backend foydalanuvchini tasdiqlaydi, XP'ni bazada yangilaydi va
    joriy holatni qaytaradi — shu bilan XP endi sahifa yopilganda yo'qolmaydi.
    """
    try:
        body = await request.json()
    except Exception:
        return cors_response({"error": "invalid_json"}, status=400)

    user = verify_init_data(body.get("initData", ""))
    if not user or "id" not in user:
        return cors_response({"error": "unauthorized"}, status=401)

    user_id = user["id"]
    name = user.get("first_name", "Foydalanuvchi")
    xp_delta = int(body.get("xp_delta", 0) or 0)

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute("SELECT xp, is_premium FROM zukko_users WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    if row is None:
        current_xp = max(xp_delta, 0)
        is_premium = False
        cursor.execute(
            "INSERT INTO zukko_users (user_id, name, xp, parent_id, is_premium) VALUES (%s, %s, %s, NULL, FALSE)",
            (user_id, name, current_xp)
        )
    else:
        current_xp = max(row[0] + xp_delta, 0)
        is_premium = row[1]
        cursor.execute(
            "UPDATE zukko_users SET xp = %s, name = %s WHERE user_id = %s",
            (current_xp, name, user_id)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return cors_response({
        "name": name,
        "xp": current_xp,
        "is_premium": is_premium
    })


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_post("/api/sync", handle_sync)
    app.router.add_options("/api/sync", handle_options)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi")


async def main():
    logging.basicConfig(level=logging.INFO)
    await start_web_server()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
