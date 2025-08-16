import os
import sqlite3
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

# 🎁 Ball qo‘shish
def add_points(user_id, amount):
    try:
        cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
    except Exception as e:
        print(f"Xatolik add_points: {e}")

# 🗂 Foydalanuvchini bazaga qo‘shish
def register_user(user_id):
    try:
        cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except Exception as e:
        print(f"Xatolik register_user: {e}")

# 🔘 Start menyusi tugmalari
def start_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💬 Suhbat", callback_data="chat"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus"),
        InlineKeyboardButton("👤 Profil", callback_data="profile"),
        InlineKeyboardButton("🏆 Reyting", callback_data="top"),
        InlineKeyboardButton("ℹ️ VIP haqida", callback_data="vip_info")
    )
    return keyboard

# 🚀 START komandasi
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    register_user(user_id)
    await message.answer(
        "👋 Assalomu alaykum, Chat360 ga xush kelibsiz!\n\n"
        "🔹 Quyidagi tugmalar orqali botni boshqarishingiz mumkin:\n\n"
        "💬 Suhbat — tasodifiy odamlar bilan chat\n"
        "🎁 Bonus — har kuni ball oling\n"
        "👤 Profil — o‘z ballingiz va statusingizni ko‘ring\n"
        "🏆 Reyting — TOP foydalanuvchilar\n"
        "ℹ️ VIP haqida — VIP tizimi haqida ma’lumot",
        reply_markup=start_keyboard()
    )

# 👤 PROFILE komandasi
@dp.message_handler(commands=['profile'])
async def profile_cmd(message: types.Message):
    user_id = message.from_user.id
    try:
        cur.execute("SELECT points, referrals, status FROM users WHERE user_id = ?", (user_id,))
        data = cur.fetchone()

        if data:
            points, referrals, status = data
            status_display = "⭐ VIP" if status == "VIP" else "🔹 Normal"
            await message.answer(
                f"👤 Profilingiz:\n\n"
                f"⭐ Ball: {points}\n"
                f"👥 Referral: {referrals} ta\n"
                f"🔥 Status: {status_display}\n\n"
                f"💬 VIP foydalanuvchilar maxsus chatlarda qizlar bilan suhbatlashadi.",
                reply_markup=start_keyboard()
            )
        else:
            await message.answer("❌ Profil topilmadi. /start bosing.")
    except Exception as e:
        print(f"Xatolik profile_cmd: {e}")

# 🎁 BONUS komandasi
@dp.message_handler(commands=['bonus'])
async def bonus_cmd(message: types.Message):
    user_id = message.from_user.id
    today = str(datetime.date.today())
    try:
        cur.execute("SELECT last_bonus, points, status FROM users WHERE user_id = ?", (user_id,))
        last_bonus, points, status = cur.fetchone()

        if last_bonus == today:
            await message.answer("❌ Siz bugungi bonusni oldingiz.")
        else:
            add_points(user_id, 10)
            points += 10
            cur.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (today, user_id))
            # VIP holatini tekshirish
            if points >= 100 and status != 'VIP':
                cur.execute("UPDATE users SET status = 'VIP' WHERE user_id = ?", (user_id,))
                await message.answer("🎉 Tabriklaymiz! Siz VIP bo‘ldingiz!")
            conn.commit()
            await message.answer("🎁 Siz 10 ball oldingiz!")
    except Exception as e:
        print(f"Xatolik bonus_cmd: {e}")

# 💬 CHAT komandasi (VIP tekshiradi)
@dp.message_handler(commands=['chat'])
async def chat_cmd(message):
    user_id = message.from_user.id
    try:
        cur.execute("SELECT points, status FROM users WHERE user_id = ?", (user_id,))
        points, status = cur.fetchone()
        if status != "VIP":
            await message.answer("⚠️ Siz hali VIP emassiz. VIP chatlar faqat 100 ball to‘plagan foydalanuvchilar uchun!")
            return

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
    except Exception as e:
        print(f"Xatolik chat_cmd: {e}")

# 🛑 STOP komandasi
@dp.message_handler(commands=['stop'])
async def stop_cmd(message):
    user_id = message.from_user.id
    try:
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
    except Exception as e:
        print(f"Xatolik stop_cmd: {e}")

# ⏭ NEXT komandasi
@dp.message_handler(commands=['next'])
async def next_cmd(message):
    await stop_cmd(message)
    await chat_cmd(message)

# 🏆 TOP komandasi
@dp.message_handler(commands=['top'])
async def top_cmd(message: types.Message):
    try:
        cur.execute("SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10")
        top_users = cur.fetchall()
        text = "🏆 Reyting TOP-10:\n\n"
        for i, (uid, points) in enumerate(top_users, start=1):
            text += f"{i}. 👤 {uid} — ⭐ {points} ball\n"
        await message.answer(text)
    except Exception as e:
        print(f"Xatolik top_cmd: {e}")

# 📩 Callback tugmalarni ishlatish
@dp.callback_query_handler(lambda c: True)
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "chat":
        await chat_cmd(callback_query.message)
    elif data == "bonus":
        await bonus_cmd(callback_query.message)
    elif data == "profile":
        await profile_cmd(callback_query.message)
    elif data == "top":
        await top_cmd(callback_query.message)
    elif data == "vip_info":
        await callback_query.message.answer(
            "💬 VIP tizimi:\n"
            "✅ Har kuni /bonus orqali ball yig‘ing.\n"
            "✅ 100 ball to‘plaganingizda siz VIP bo‘lasiz.\n"
            "✅ VIP foydalanuvchilar maxsus chatlarda qizlar bilan suhbatlashadi!"
        )
    else:
        await callback_query.message.answer("❌ Noma'lum tugma.")
    await callback_query.answer()

# 📩 Xabar yuborish (suhbat ichida)
@dp.message_handler()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
        partner = cur.fetchone()
        if partner:
            partner_id = partner[0]
            try:
                await bot.send_message(partner_id, message.text)
            except:
                await message.answer("⚠️ Xabar yuborilmadi, suhbatdosh offline.")
        else:
            await message.answer("⚠️ Siz hozir suhbatda emassiz. /chat bilan boshlang.")
    except Exception as e:
        print(f"Xatolik chat_handler: {e}")

# 🚀 BOT ISHGA TUSHIRISH
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
