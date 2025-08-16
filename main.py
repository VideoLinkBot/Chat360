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

# ⏳ Waiting list (status ustuni qo‘shildi)
cur.execute("""
CREATE TABLE IF NOT EXISTS waiting (
    user_id INTEGER PRIMARY KEY,
    want_gender TEXT DEFAULT 'any',
    status TEXT DEFAULT 'Normal'
)
""")

conn.commit()

# 🎁 Foydalanuvchiga ball qo‘shish
def add_points(user_id, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    update_status(user_id)

# 🗂 Foydalanuvchini bazaga qo‘shish
def register_user(user_id):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

# 🏅 Statusni yangilash
def update_status(user_id):
    cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    points = cur.fetchone()[0]

    if points >= 150:
        status = 'VIP'
    elif points >= 100:
        status = 'Gold'
    elif points >= 70:
        status = 'Silver'
    elif points >= 40:
        status = 'Bronze'
    else:
        status = 'Normal'

    cur.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()

# ================= Til tanlash =================
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz")
    await message.answer("👋 Assalomu alaykum! Tilni tanlang / Choose language / Выберите язык:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz"])
async def set_language(message: types.Message):
    lang_map = {"🇺🇿 O‘zbek": "uz", "🇷🇺 Rus": "ru", "🇬🇧 Ingliz": "en"}
    lang = lang_map[message.text]
    user_id = message.from_user.id
    cur.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()

    if lang == "uz":
        text = (
            "💬 /chat — Suhbatdosh topish\n"
            "⏭ /next — Keyingi suhbatdosh\n"
            "🛑 /stop — Suhbatni to‘xtatish\n"
            "👤 /profile — Profilingiz\n"
            "🎁 /bonus — Kunlik bonus\n"
            "🏆 /top — Reyting\n"
            "📌 /status — Status tushuntirish"
        )
    elif lang == "ru":
        text = (
            "💬 /chat — Найти собеседника\n"
            "⏭ /next — Следующий собеседник\n"
            "🛑 /stop — Остановить чат\n"
            "👤 /profile — Ваш профиль\n"
            "🎁 /bonus — Ежедневный бонус\n"
            "🏆 /top — Рейтинг\n"
            "📌 /status — Описание статусов"
        )
    else:
        text = (
            "💬 /chat — Find a chat partner\n"
            "⏭ /next — Next partner\n"
            "🛑 /stop — Stop chat\n"
            "👤 /profile — Your profile\n"
            "🎁 /bonus — Daily bonus\n"
            "🏆 /top — Ranking\n"
            "📌 /status — Status explanation"
        )

    await message.answer(f"✅ Til o‘rnatildi: {lang.upper()}\n\n{text}")

# ================= Kunlik bonus =================
@dp.message_handler(commands=['bonus'])
async def bonus_cmd(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    cur.execute("SELECT last_bonus, status FROM users WHERE user_id = ?", (user_id,))
    last_bonus, status = cur.fetchone()

    if last_bonus == today:
        await message.answer("❌ Siz bugungi bonusni oldingiz.")
    else:
        # Statusga qarab ball
        status_bonus = {
            'Normal': (3,5),
            'Bronze': (5,8),
            'Silver': (8,12),
            'Gold': (12,15),
            'VIP': (15,20)
        }
        low, high = status_bonus.get(status, (3,5))
        points = random.randint(low, high)
        add_points(user_id, points)
        cur.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        await message.answer(f"🎁 Tabriklaymiz! Siz {points} ball oldingiz. Statusingiz: {status}")

# ================= Profile =================
@dp.message_handler(commands=['profile'])
async def profile_cmd(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT points, referrals, status FROM users WHERE user_id = ?", (user_id,))
    data = cur.fetchone()
    if data:
        points, referrals, status = data
        status_emoji = {
            'Normal':'⚪', 'Bronze':'🟫', 'Silver':'🟦', 'Gold':'🟨', 'VIP':'🟪'
        }
        await message.answer(
            f"{status_emoji.get(status,'⚪')} Profilingiz:\n\n"
            f"⭐ Ball: {points}\n"
            f"👥 Referral: {referrals} ta\n"
            f"🔥 Status: {status}"
        )
    else:
        await message.answer("❌ Profil topilmadi. /start bosing.")

# ================= Status tushuntirish =================
@dp.message_handler(commands=['status'])
async def status_info(message: types.Message):
    text = (
        "🔥 Chat360 Status Tizimi:\n\n"
        "⚪ Normal — Har kuni 3–5 ball\n"
        "🟫 Bronze — Har kuni 5–8 ball\n"
        "🟦 Silver — Har kuni 8–12 ball\n"
        "🟨 Gold — Har kuni 12–15 ball\n"
        "🟪 VIP — Har kuni 15–20 ball\n\n"
        "⭐ Status qanchalik yuqori bo‘lsa, chat tezroq topiladi va profil boshqalardan ajralib turadi!"
    )
    await message.answer(text)

# ================= CHAT komandasi (VIP tezlik qo‘shildi) =================
@dp.message_handler(commands=['chat'])
async def chat_cmd(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
    status = cur.fetchone()[0]

    # Foydalanuvchini waiting ga status bilan qo'shamiz
    cur.execute("INSERT OR REPLACE INTO waiting (user_id, status) VALUES (?, ?)", (user_id, status))
    conn.commit()

    # Statusga qarab ustuvorlik: VIP > Gold > Silver > Bronze > Normal
    priority = ['VIP','Gold','Silver','Bronze','Normal']
    partner = None
    for s in priority:
        if s == status:
            continue
        cur.execute("SELECT user_id FROM waiting WHERE user_id != ? AND status = ? ORDER BY user_id LIMIT 1", (user_id, s))
        partner = cur.fetchone()
        if partner:
            break

    # Shu statusdagi foydalanuvchilar orasidan topilmasa o'z statusida qidiring
    if not partner:
        cur.execute("SELECT user_id FROM waiting WHERE user_id != ? AND status = ? ORDER BY user_id LIMIT 1", (user_id, status))
        partner = cur.fetchone()

    if partner:
        partner_id = partner[0]
        # Active chats va waiting dan o'chirish
        cur.execute("DELETE FROM waiting WHERE user_id IN (?, ?)", (user_id, partner_id))
        cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (user_id, partner_id))
        cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (partner_id, user_id))
        conn.commit()
        await bot.send_message(user_id, "✅ Suhbatdosh topildi! 💬")
        await bot.send_message(partner_id, "✅ Suhbatdosh topildi! 💬")
    else:
        await message.answer("⏳ Suhbatdosh qidirilmoqda...")

# ================= STOP =================
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

# ================= NEXT =================
@dp.message_handler(commands=['next'])
async def next_cmd(message: types.Message):
    await stop_cmd(message)
    await chat_cmd(message)

# ================= TOP =================
@dp.message_handler(commands=['top'])
async def top_cmd(message: types.Message):
    cur.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    top_users = cur.fetchall()
    text = "🏆 Reyting TOP-10:\n\n"
    for i, (uid, points) in enumerate(top_users, start=1):
        text += f"{i}. 👤 {uid} — ⭐ {points} ball\n"
    await message.answer(text)

# ================= Oddiy matn xabarlar =================
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
