   import os
import sqlite3
import random
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# 🔑 Token environment variables'dan olinadi
API_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 📂 SQLite baza
conn = sqlite3.connect("chat360.db", check_same_thread=False)
cur = conn.cursor()

# 👤 Users jadvali
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    gender TEXT DEFAULT 'none',
    points INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    status TEXT DEFAULT 'normal',
    want_gender TEXT DEFAULT 'any',
    country TEXT DEFAULT 'unknown',
    lang TEXT DEFAULT 'unknown',
    last_bonus TEXT DEFAULT ''
)
""")

# 🔗 Active chats
cur.execute("""
CREATE TABLE IF NOT EXISTS active_chats (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER
)
""")

# ⏳ Waiting list
cur.execute("""
CREATE TABLE IF NOT EXISTS waiting (
    user_id INTEGER PRIMARY KEY,
    want_gender TEXT DEFAULT 'any'
)
""")

conn.commit()

# 🎁 Foydalanuvchiga ball qo‘shish
def add_points(user_id, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

# 🗂 Foydalanuvchini bazaga qo‘shish
def register_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# ===================== Qo‘shimcha funksiyalar =====================

# 1️⃣ Referral tizimi
def register_user_with_ref(user_id, referrer_id=None):
    register_user(user_id)
    if referrer_id and referrer_id != user_id:
        cur.execute("UPDATE users SET referrals = referrals + 1, points = points + 5 WHERE user_id = ?", (referrer_id,))
        conn.commit()

# 2️⃣ Kunlik bonus (tasodifiy)
@dp.message_handler(commands=['bonus'])
async def bonus_cmd_random(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())

    cur.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
    last_bonus = cur.fetchone()[0]

    if last_bonus == today:
        await message.answer("❌ Siz bugungi bonusni oldingiz.")
    else:
        bonus_points = random.choice([5, 10, 15])
        add_points(user_id, bonus_points)
        cur.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        await message.answer(f"🎁 Tabriklaymiz! Siz {bonus_points} ball oldingiz.")

# ===================== TIL TANLASH VA BOSHLANGICH DIZAYN =====================

# Til tanlash tugmalari
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz")

    await message.answer("🔧 Tilni tanlang / Choose language / Выберите язык:", reply_markup=keyboard)

# Tilni saqlash va boshlangich dizayn chiqarish
@dp.message_handler(lambda message: message.text in ["🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz"])
async def set_language(message: types.Message):
    user_id = message.from_user.id
    lang_map = {"🇺🇿 O‘zbek": "uz", "🇷🇺 Rus": "ru", "🇬🇧 Ingliz": "en"}
    lang = lang_map[message.text]
    cur.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()

    # Tanlangan tilga mos start matni
    if lang == "uz":
        text = (
            "👋 Assalomu alaykum, Chat360 ga xush kelibsiz!\n\n"
            "💬 /chat — Suhbatdosh topish\n"
            "⏭ /next — Keyingi suhbatdosh\n"
            "🛑 /stop — Suhbatni to‘xtatish\n"
            "👤 /profile — Profilingiz\n"
            "🎁 /bonus — Kunlik bonus\n"
            "🏆 /top — Reyting\n"
        )
    elif lang == "ru":
        text = (
            "👋 Добро пожаловать в Chat360!\n\n"
            "💬 /chat — Найти собеседника\n"
            "⏭ /next — Следующий собеседник\n"
            "🛑 /stop — Остановить чат\n"
            "👤 /profile — Ваш профиль\n"
            "🎁 /bonus — Ежедневный бонус\n"
            "🏆 /top — Рейтинг\n"
        )
    else:  # en
        text = (
            "👋 Welcome to Chat360!\n\n"
            "💬 /chat — Find a chat partner\n"
            "⏭ /next — Next partner\n"
            "🛑 /stop — Stop chat\n"
            "👤 /profile — Your profile\n"
            "🎁 /bonus — Daily bonus\n"
            "🏆 /top — Rating\n"
        )

    await message.answer(text)

# 👤 PROFILE komandasi
@dp.message_handler(commands=['profile'])
async def profile_cmd(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT points, referrals, status FROM users WHERE user_id = ?", (user_id,))
    data = cur.fetchone()

    if data:
        points, referrals, status = data
        await message.answer(
            f"👤 Profilingiz:\n\n"
            f"⭐ Ball: {points}\n"
            f"👥 Referral: {referrals} ta\n"
            f"🔥 Status: {status}\n"
        )
    else:
        await message.answer("❌ Profil topilmadi. /start bosing.")

# 💬 CHAT komandasi
@dp.message_handler(commands=['chat'])
async def chat_cmd(message: types.Message):
    user_id = message.from_user.id

    # Agar kutayotganlar bo‘lsa, ulash
    cur.execute("SELECT user_id FROM waiting WHERE user_id != ? LIMIT 1", (user_id,))
    partner = cur.fetchone()

    if partner:
        partner_id = partner[0]
        cur.execute("DELETE FROM waiting WHERE user_id IN (?, ?)", (user_id, partner_id))
        cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (user_id, partner_id))
        cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (partner_id, user_id))
        conn.commit()

        await bot.send_message(user_id, "✅ Suhbatdosh topildi! 💬")
        await bot.send_message(partner_id, "✅ Suhbatdosh topildi! 💬")
    else:
        # Kutish ro‘yxatiga qo‘shamiz
        cur.execute("INSERT OR REPLACE INTO waiting (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await message.answer("⏳ Suhbatdosh qidirilmoqda...")

# 🛑 STOP komandasi
@dp.message_handler(commands=['stop'])
async def stop_cmd(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    partner = cur.fetchone()

    if partner:
        partner_id = partner[0]
        cur.execute("DELETE FROM active_chats WHERE user_id IN (?, ?)", (user_id, partner_id))
        conn.commit()
        await bot.send_message(user_id, "❌ Suhbat tugatildi.")
        await bot.send_message(partner_id, "❌ Suhbat tugatildi.")
    else:
        await message.answer("⚠️ Siz hozir suhbatda emassiz.")

# ⏭ NEXT komandasi
@dp.message_handler(commands=['next'])
async def next_cmd(message: types.Message):
    user_id = message.from_user.id
    await stop_cmd(message)  # Avvalgi suhbatni tugatish
    await chat_cmd(message)  # Yangi suhbat qidirish

# 🏆 TOP komandasi
@dp.message_handler(commands=['top'])
async def top_cmd(message: types.Message):
    cur.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    top_users = cur.fetchall()

    text = "🏆 Reyting TOP-10:\n\n"
    for i, (uid, points) in enumerate(top_users, start=1):
        text += f"{i}. 👤 {uid} — ⭐ {points} ball\n"

    await message.answer(text)

# 📩 Oddiy matn xabarlar (faqat suhbatda)
@dp.message_handler()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    partner = cur.fetchone()

    if partner:
        partner_id = partner[0]
        await bot.send_message(partner_id, message.text)

# 🚀 BOT ISHGA TUSHIRISH
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True) 
