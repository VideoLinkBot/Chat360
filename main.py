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
    status TEXT DEFAULT 'Normal',
    want_gender TEXT DEFAULT 'any',
    country TEXT DEFAULT 'unknown',
    lang TEXT DEFAULT 'uz',
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

# 👤 Foydalanuvchini bazaga qo‘shish
def register_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# 🔄 Status yangilash
def update_status(user_id):
    cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    points = cur.fetchone()[0]
    if points >= 200:
        status = "Gold 🟡"
    elif points >= 100:
        status = "Silver ⚪"
    elif points >= 50:
        status = "Bronze 🟤"
    else:
        status = "Normal ⚪"
    cur.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    return status

# ===================== Til tanlash =====================
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id)

    # Til tanlash klaviaturasi
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz")
    await message.answer("Tilni tanlang / Выберите язык / Choose language:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz"])
async def set_language(message: types.Message):
    lang_map = {"🇺🇿 O‘zbek": "uz", "🇷🇺 Rus": "ru", "🇬🇧 Ingliz": "en"}
    lang = lang_map[message.text]
    user_id = message.from_user.id
    cur.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()

    # Boshlang‘ich xabar tilga mos
    if lang == "uz":
        text = (
            "👋 Assalomu alaykum, Chat360 ga xush kelibsiz!\n\n"
            "💎 Status tizimi:\n"
            "⚪ Normal — boshlang‘ich foydalanuvchi\n"
            "🟤 Bronze — 50 ball\n"
            "⚪ Silver — 100 ball\n"
            "🟡 Gold / VIP — 200+ ball\n\n"
            "🏆 Status foydalanuvchiga:\n"
            "- Tezroq suhbat topish\n"
            "- Ko‘proq bonus ball olish\n"
            "- Profilida maxsus emoji ko‘rinishi\n\n"
            "💬 /chat — Suhbatdosh topish\n"
            "⏭ /next — Keyingi suhbatdosh\n"
            "🛑 /stop — Suhbatni to‘xtatish\n"
            "👤 /profile — Profilingiz\n"
            "🎁 /bonus — Kunlik bonus\n"
            "🏆 /top — Reyting\n"
        )
    elif lang == "ru":
        text = (
            "👋 Приветствуем в Chat360!\n\n"
            "💎 Система статусов:\n"
            "⚪ Normal — новичок\n"
            "🟤 Bronze — 50 очков\n"
            "⚪ Silver — 100 очков\n"
            "🟡 Gold / VIP — 200+ очков\n\n"
            "🏆 Преимущества:\n"
            "- Быстро найти собеседника\n"
            "- Получать больше бонусных очков\n"
            "- Специальный emoji в профиле\n\n"
            "💬 /chat — Найти собеседника\n"
            "⏭ /next — Следующий собеседник\n"
            "🛑 /stop — Остановить чат\n"
            "👤 /profile — Профиль\n"
            "🎁 /bonus — Ежедневный бонус\n"
            "🏆 /top — Рейтинг\n"
        )
    else:
        text = (
            "👋 Welcome to Chat360!\n\n"
            "💎 Status system:\n"
            "⚪ Normal — beginner\n"
            "🟤 Bronze — 50 points\n"
            "⚪ Silver — 100 points\n"
            "🟡 Gold / VIP — 200+ points\n\n"
            "🏆 Advantages:\n"
            "- Find a chat partner faster\n"
            "- Earn more bonus points\n"
            "- Special emoji in profile\n\n"
            "💬 /chat — Find a partner\n"
            "⏭ /next — Next partner\n"
            "🛑 /stop — Stop chat\n"
            "👤 /profile — Your profile\n"
            "🎁 /bonus — Daily bonus\n"
            "🏆 /top — Leaderboard\n"
        )

    await message.answer(text)

# ===================== Kunlik bonus =====================
@dp.message_handler(commands=['bonus'])
async def bonus_cmd(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())

    cur.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
    last_bonus = cur.fetchone()[0]

    if last_bonus == today:
        await message.answer("❌ Siz bugungi bonusni oldingiz.")
    else:
        cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        points = cur.fetchone()[0]

        # Statusga mos bonus
        if points >= 200:
            bonus_points = random.choice([20, 25, 30])
        elif points >= 100:
            bonus_points = random.choice([15, 20])
        elif points >= 50:
            bonus_points = random.choice([10, 15])
        else:
            bonus_points = random.choice([5, 10])

        add_points(user_id, bonus_points)
        cur.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (today, user_id))
        conn.commit()

        # Statusni yangilash
        status = update_status(user_id)
        await message.answer(f"🎁 Siz {bonus_points} ball oldingiz!\n🔥 Statusingiz: {status}")

# ===================== PROFILE =====================
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

# ===================== CHAT / NEXT / STOP / TOP =====================
@dp.message_handler(commands=['chat'])
async def chat_cmd(message: types.Message):
    user_id = message.from_user.id

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
        cur.execute("INSERT OR REPLACE INTO waiting (user_id) VALUES (?)", (user_id,))
        conn.commit()
        await message.answer("⏳ Suhbatdosh qidirilmoqda...")

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

@dp.message_handler(commands=['next'])
async def next_cmd(message: types.Message):
    await stop_cmd(message)
    await chat_cmd(message)

@dp.message_handler(commands=['top'])
async def top_cmd(message: types.Message):
    cur.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    top_users = cur.fetchall()
    text = "🏆 Reyting TOP-10:\n\n"
    for i, (uid, points) in enumerate(top_users, start=1):
        text += f"{i}. 👤 {uid} — ⭐ {points} ball\n"
    await message.answer(text)

# ===================== Suhbat matni =====================
@dp.message_handler()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    partner = cur.fetchone()
    if partner:
        partner_id = partner[0]
        await bot.send_message(partner_id, message.text)

# ===================== BOT ISHGA TUSHIRISH =====================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
