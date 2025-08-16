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
    want_gender TEXT DEFAULT 'any',
    country TEXT DEFAULT 'unknown',
    lang TEXT DEFAULT 'uz',
    points INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    status TEXT DEFAULT 'normal',
    last_bonus TEXT DEFAULT ''
)
""")

# 🔗 Active chats
cur.execute("""
CREATE TABLE IF NOT EXISTS active_chats (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ⏳ Waiting list
cur.execute("""
CREATE TABLE IF NOT EXISTS waiting (
    user_id INTEGER PRIMARY KEY,
    want_gender TEXT DEFAULT 'any',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# 🎁 Foydalanuvchiga ball qo‘shish
def add_points(user_id, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

# 🗂 Foydalanuvchini bazaga qo‘shish
def register_user(user_id, referrer_id=None):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    # Referral tizimi
    if referrer_id and referrer_id != user_id:
        cur.execute("UPDATE users SET referrals = referrals + 1, points = points + 5 WHERE user_id = ?", (referrer_id,))
        conn.commit()

# 🌐 Til tanlash
async def ask_language(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        types.InlineKeyboardButton("🇺🇿 Uzbek", callback_data="lang_uz"),
        types.InlineKeyboardButton("🇷🇺 Russian", callback_data="lang_ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    await message.answer("Tilni tanlang / Select language:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('lang_'))
async def process_language(callback_query: types.CallbackQuery):
    lang = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    cur.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    await bot.answer_callback_query(callback_query.id, text=f"Til o‘rnatildi: {lang.upper()}")
    await bot.send_message(user_id, "✅ Siz tayyorsiz! /chat bilan suhbat boshlang.")

# 🚀 START komandasi
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id

    # Referral ID olish
    args = message.get_args()
    referrer_id = int(args) if args.isdigit() else None

    register_user(user_id, referrer_id)
    await ask_language(message)

# 👤 PROFILE komandasi
@dp.message_handler(commands=['profile'])
async def profile_cmd(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT points, referrals, status, gender, want_gender, country, lang FROM users WHERE user_id = ?", (user_id,))
    data = cur.fetchone()

    if data:
        points, referrals, status, gender, want_gender, country, lang = data
        await message.answer(
            f"👤 Profilingiz:\n\n"
            f"⭐ Ball: {points}\n"
            f"👥 Referral: {referrals} ta\n"
            f"🔥 Status: {status}\n"
            f"⚥ Jins: {gender}\n"
            f"🔎 Qidirilayotgan jins: {want_gender}\n"
            f"🌍 Mamlakat: {country}\n"
            f"🗣 Til: {lang}\n"
        )
    else:
        await message.answer("❌ Profil topilmadi. /start bosing.")

# 🎁 BONUS komandasi
@dp.message_handler(commands=['bonus'])
async def bonus_cmd(message: types.Message):
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
    await stop_cmd(message)
    await chat_cmd(message)

# 🏆 TOP komandasi
@dp.message_handler(commands=['top'])
async def top_cmd(message: types.Message):
    cur.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
    top_users = cur.fetchall()

    text = "🏆 Reyting TOP-10:\n\n"
    for i, (uid, points) in enumerate(top_users, start=1):
        text += f"{i}. 👤 {uid} — ⭐ {points} ball\n"

    await message.answer(text)

# ⚙ SETTINGS komandasi
@dp.message_handler(commands=['settings'])
async def settings_cmd(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🔄 O‘zgartirish: jins", "🔄 O‘zgartirish: qidiriladigan jins", "🔄 O‘zgartirish: til")
    await message.answer("⚙ Sozlamalar:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text.startswith("🔄 O‘zgartirish"))
async def change_settings(message: types.Message):
    user_id = message.from_user.id
    if "jins" in message.text:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("♂ Erkak", callback_data="set_gender_male"),
            types.InlineKeyboardButton("♀ Ayol", callback_data="set_gender_female"),
            types.InlineKeyboardButton("⚧ Boshqa", callback_data="set_gender_other")
        )
        await message.answer("Jinsni tanlang:", reply_markup=keyboard)
    elif "qidiriladigan jins" in message.text:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("♂ Erkak", callback_data="set_want_male"),
            types.InlineKeyboardButton("♀ Ayol", callback_data="set_want_female"),
            types.InlineKeyboardButton("⚧ Har qanday", callback_data="set_want_any")
        )
        await message.answer("Qidiriladigan jinsni tanlang:", reply_markup=keyboard)
    elif "til" in message.text:
        await ask_language(message)

@dp.callback_query_handler(lambda c: c.data.startswith("set_"))
async def process_setting(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    if data.startswith("set_gender_"):
        gender = data.split("_")[-1]
        cur.execute("UPDATE users SET gender = ? WHERE user_id = ?", (gender, user_id))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, text=f"Jins o‘zgartirildi: {gender}")
    elif data.startswith("set_want_"):
        want_gender = data.split("_")[-1]
        cur.execute("UPDATE users SET want_gender = ? WHERE user_id = ?", (want_gender, user_id))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, text=f"Qidiriladigan jins o‘zgartirildi: {want_gender}")

# 📩 Xabar yuborish (faqat suhbat ichida)
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    partner = cur.fetchone()
    if partner:
        partner_id = partner[0]
        # Text, photo, video, voice va boshqa xabarlarni yuborish
        if message.content_type == 'text':
            await bot.send_message(partner_id, message.text)
        elif message.content_type == 'photo':
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.content_type == 'video':
            await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.content_type == 'voice':
            await bot.send_voice(partner_id, message.voice.file_id)
        else:
            await bot.send_message(user_id, "⚠️ Bu turdagi xabar hali qo‘llab-quvvatlanmaydi.")
    else:
        await message.answer("⚠️ Siz hozir suhbatda emassiz.")

# 🚀 BOT ISHGA TUSHIRISH
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
