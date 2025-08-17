import os
import sqlite3
import random
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# 🔑 Token environment variables'dan olinadi
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    print("❌ BOT_TOKEN muhit o‘zgaruvchisi topilmadi!")
    exit()

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

# === NEW: foydalanuvchi nomlarini saqlash uchun maydonlar (migration yengil usul) ===
try:
    cur.execute("ALTER TABLE users ADD COLUMN username TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass
try:
    cur.execute("ALTER TABLE users ADD COLUMN first_name TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass

# 🔗 Active chats
cur.execute("""
CREATE TABLE IF NOT EXISTS active_chats (
    user_id INTEGER PRIMARY KEY,
    partner_id INTEGER
)
""")

# ⏳ Waiting list (gender va status qo‘shildi)
cur.execute("""
CREATE TABLE IF NOT EXISTS waiting (
    user_id INTEGER PRIMARY KEY,
    gender TEXT DEFAULT 'none',
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
def register_user(user_id, username="", first_name=""):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    # doimiy yangilab turamiz (username o‘zgarishi mumkin)
    cur.execute("UPDATE users SET username=?, first_name=? WHERE user_id=?",
                (username or "", first_name or "", user_id))
    conn.commit()

# 🏅 Statusni yangilash
def update_status(user_id):
    cur.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    points = row[0] if row else 0

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

# ================= Til tanlash + Referral =================
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = (message.from_user.username or "") if message.from_user else ""
    first_name = (message.from_user.first_name or "") if message.from_user else ""
    register_user(user_id, username, first_name)

    # === NEW: referral deep-link qayd qilish ===
    parts = message.text.split(maxsplit=1)
    if len(parts) == 2:
        payload = parts[1].strip()
        if payload.isdigit():
            inviter_id = int(payload)
            if inviter_id != user_id:
                # faqat birinchi marta hisoblash uchun: agar foydalanuvchi yangimi?
                cur.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
                exists = cur.fetchone()
                # Garantiyaga: faqat yangi userlarni "birinchi marta kirganda" referal qilish
                # (oddiy holatda INSERT OR IGNORE yuqorida bajarilgan, shuning uchun
                # foydalanuvchi yangiligi bo'yicha sodda tekshiruvga o'tamiz)
                # Yon ta'sirlarni oldini olish uchun tekshiramiz: agar points/referrals hammasi 0 bo'lsa - yangi deymiz
                cur.execute("SELECT points, referrals FROM users WHERE user_id=?", (user_id,))
                p_r = cur.fetchone()
                if p_r and (p_r[0] == 0 and p_r[1] == 0):
                    cur.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id=?", (inviter_id,))
                    conn.commit()
                    try:
                        await bot.send_message(inviter_id, "👥 Sizning referalingiz orqali yangi foydalanuvchi kirdi! +1")
                    except:
                        pass

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz")
    await message.answer("👋 Assalomu alaykum! Tilni tanlang / Choose language / Выберите язык:", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["🇺🇿 O‘zbek", "🇷🇺 Rus", "🇬🇧 Ingliz"])
async def set_language(message: types.Message):
    lang_map = {"🇺🇿 O‘zbek": "uz", "🇷🇺 Rus": "ru", "🇬🇧 Ingliz": "en"}
    lang = lang_map[message.text]
    user_id = message.from_user.id
    cur.execute("UPDATE users SET lang = ?, username=?, first_name=? WHERE user_id = ?",
                (lang, message.from_user.username or "", message.from_user.first_name or "", user_id))
    conn.commit()

    if lang == "uz":
        text = (
            "💬 /chat — Suhbatdosh topish\n"
            "⏭ /next — Keyingi suhbatdosh\n"
            "🛑 /stop — Suhbatni to‘xtatish\n"
            "👤 /profile — Profilingiz\n"
            "🎁 /bonus — Kunlik bonus\n"
            "🏆 /top — Reyting\n"
            "📌 /status — Status tushuntirish\n"
            "⚙️ /set_gender — Jinsingiz\n"
            "🎯 /set_want — Kim bilan suhbat (any/male/female)"
        )
        help_text = (
            "👋 Assalomu alaykum! Chat360 – tez va qiziqarli suhbat bot.\n"
            "💎 Statuslar: Normal, Bronze, Silver, Gold, VIP.\n"
            "⭐ Kunlik bonuslar bilan ball to‘plang, status oshadi.\n"
            "⚡ Yuqori status – tezroq matching.\n"
            "🔗 Do‘st chaqirish: /ref"
        )
    elif lang == "ru":
        text = (
            "💬 /chat — Найти собеседника\n"
            "⏭ /next — Следующий собеседник\n"
            "🛑 /stop — Остановить чат\n"
            "👤 /profile — Ваш профиль\n"
            "🎁 /bonus — Ежедневный бонус\n"
            "🏆 /top — Рейтинг\n"
            "📌 /status — Описание статусов\n"
            "⚙️ /set_gender — Ваш пол\n"
            "🎯 /set_want — Кого искать (any/male/female)"
        )
        help_text = (
            "👋 Привет! Chat360 – быстрый и удобный чат-бот.\n"
            "💎 Статусы: Normal, Bronze, Silver, Gold, VIP.\n"
            "⭐ Собирайте бонусы, повышайте статус.\n"
            "⚡ Чем выше статус, тем быстрее поиск.\n"
            "🔗 Реферал: /ref"
        )
    else:
        text = (
            "💬 /chat — Find a partner\n"
            "⏭ /next — Next partner\n"
            "🛑 /stop — Stop chat\n"
            "👤 /profile — Your profile\n"
            "🎁 /bonus — Daily bonus\n"
            "🏆 /top — Ranking\n"
            "📌 /status — Status info\n"
            "⚙️ /set_gender — Your gender\n"
            "🎯 /set_want — Preferred partner (any/male/female)"
        )
        help_text = (
            "👋 Welcome to Chat360.\n"
            "💎 Statuses: Normal → VIP.\n"
            "⭐ Collect daily bonuses to level up.\n"
            "⚡ Higher status, faster matching.\n"
            "🔗 Referral: /ref"
        )

    await message.answer(f"✅ Til o‘rnatildi: {lang.upper()}\n\n{text}\n\n{help_text}")

# ================= Referral link =================
@dp.message_handler(commands=['ref'])
async def ref_cmd(message: types.Message):
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    await message.answer(f"🔗 Sizning taklif havolangiz:\n{link}\nDo‘stlaringiz bilan ulashing!")

# ================= Jins tanlash =================
@dp.message_handler(commands=['set_gender'])
async def set_gender_cmd(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("O‘g‘il", "Qiz")
    await message.answer("Siz qaysi jinsdasiz?", reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in ["O‘g‘il", "Qiz"])
async def save_gender(message: types.Message):
    user_id = message.from_user.id
    gender = "male" if message.text == "O‘g‘il" else "female"
    cur.execute("UPDATE users SET gender = ? WHERE user_id = ?", (gender, user_id))
    conn.commit()
    await message.answer(f"Sizning jinsingiz saqlandi: {message.text}", reply_markup=types.ReplyKeyboardRemove())

# ================= NEW: Kim bilan suhbat (want_gender) =================
@dp.message_handler(commands=['set_want'])
async def set_want_cmd(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    kb.add("Any", "O‘g‘il", "Qiz")
    await message.answer("Kim bilan suhbatlashmoqchisiz? (Any/O‘g‘il/Qiz)", reply_markup=kb)

@dp.message_handler(lambda m: m.text in ["Any", "O‘g‘il", "Qiz"])
async def save_want_gender(message: types.Message):
    user_id = message.from_user.id
    mapping = {"Any": "any", "O‘g‘il": "male", "Qiz": "female"}
    want = mapping[message.text]
    cur.execute("UPDATE users SET want_gender=? WHERE user_id=?", (want, user_id))
    conn.commit()
    await message.answer(f"✅ Tanlov saqlandi: {message.text}", reply_markup=types.ReplyKeyboardRemove())

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
    cur.execute("SELECT points, referrals, status, lang, username, first_name, gender, want_gender FROM users WHERE user_id = ?", (user_id,))
    data = cur.fetchone()
    if data:
        points, referrals, status, lang, username, first_name, gender, want = data
        status_emoji = {'Normal':'⚪', 'Bronze':'🟫', 'Silver':'🟦', 'Gold':'🟨', 'VIP':'🟪'}
        uname = f"@{username}" if username else (first_name or "Noma’lum")
        gmap = {"male": "O‘g‘il", "female": "Qiz", "none": "Kiritilmagan"}
        wmap = {"any": "Har kim", "male": "O‘g‘il", "female": "Qiz"}
        await message.answer(
            f"{status_emoji.get(status,'⚪')} Profilingiz:\n\n"
            f"👤 Foydalanuvchi: {uname}\n"
            f"🌐 Til: {lang.upper() if lang!='unknown' else '—'}\n"
            f"⚧ Jins: {gmap.get(gender,'—')}\n"
            f"🎯 Tanlov: {wmap.get(want,'Har kim')}\n"
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

# ================= CHAT komandasi (yaxshilangan matching) =================
def status_priority(s: str) -> int:
    order = {"VIP": 0, "Gold": 1, "Silver": 2, "Bronze": 3, "Normal": 4}
    return order.get(s, 5)

def is_gender_ok(my_want: str, partner_gender: str) -> bool:
    # my_want: any/male/female ; partner_gender: male/female/none
    if my_want == "any" or partner_gender == "none":
        return True
    return my_want == partner_gender

@dp.message_handler(commands=['chat'])
async def chat_cmd(message: types.Message):
    user_id = message.from_user.id
    cur.execute("SELECT status, gender, want_gender FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    if not result:
        await message.answer("❌ Siz ro‘yxatda topilmadingiz. /start bosing.")
        return

    user_status, user_gender, user_want = result

    # Kutayotganlar ro'yxatini olish (o'zidan tashqari) va status bo'yicha ustuvorlik
    cur.execute("""
        SELECT user_id, gender, status FROM waiting
        WHERE user_id != ?
        ORDER BY CASE status
            WHEN 'VIP' THEN 0
            WHEN 'Gold' THEN 1
            WHEN 'Silver' THEN 2
            WHEN 'Bronze' THEN 3
            ELSE 4
        END, user_id ASC
    """, (user_id,))
    waiting_users = cur.fetchall()

    partner_id = None

    # Matching: ikkala tomon istagini tekshiramiz
    for w_id, w_gender, w_status in waiting_users:
        # waiting dagi foydalanuvchining xohishlarini ham olamiz
        cur.execute("SELECT want_gender FROM users WHERE user_id=?", (w_id,))
        row = cur.fetchone()
        w_want = row[0] if row else "any"

        ok1 = is_gender_ok(user_want, w_gender)      # menga u mosmi?
        ok2 = is_gender_ok(w_want, user_gender)      # unga men mosmanmi?
        if ok1 and ok2:
            partner_id = w_id
            break

    if partner_id:
        # Har ehtimolga: partner allaqachon chatda bo‘lsa, tashlab ketamiz
        cur.execute("SELECT partner_id FROM active_chats WHERE user_id=?", (partner_id,))
        if cur.fetchone():
            # band ekan, keyingisiga o'tamiz (oddiy usul)
            # qolgan kutayotganlar uchun qayta urinmaymiz — userni waitingga qo'shamiz
            cur.execute("INSERT OR REPLACE INTO waiting (user_id, gender, status) VALUES (?, ?, ?)",
                        (user_id, user_gender, user_status))
            conn.commit()
            await message.answer("⏳ Hozircha band, suhbatdosh qidirilmoqda...")
            return

        # Ulandi
        cur.execute("DELETE FROM waiting WHERE user_id IN (?, ?)", (user_id, partner_id))
        cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (user_id, partner_id))
        cur.execute("INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)", (partner_id, user_id))
        conn.commit()
        await bot.send_message(user_id, "✅ Suhbatdosh topildi! 💬")
        await bot.send_message(partner_id, "✅ Suhbatdosh topildi! 💬")
    else:
        # waiting jadvaliga o'zining gender va statusini qo‘shamiz
        cur.execute("INSERT OR REPLACE INTO waiting (user_id, gender, status) VALUES (?, ?, ?)",
                    (user_id, user_gender, user_status))
        conn.commit()
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
        # Ularni waiting ga qaytarmaymiz — foydalanuvchining o‘zi /chat bosadi.
    else:
        await message.answer("⚠️ Siz hozir suhbatda emassiz.")

# ================= NEXT =================
@dp.message_handler(commands=['next'])
async def next_cmd(message: types.Message):
    await stop_cmd(message)
    await chat_cmd(message)

# ================= TOP (usernames bilan) =================
@dp.message_handler(commands=['top'])
async def top_cmd(message: types.Message):
    cur.execute("SELECT user_id, points, username, first_name FROM users ORDER BY points DESC LIMIT 10")
    top_users = cur.fetchall()
    text = "🏆 Reyting TOP-10:\n\n"
    for i, (uid, points, username, first_name) in enumerate(top_users, start=1):
        name = f"@{username}" if username else (first_name or str(uid))
        text += f"{i}. {name} — ⭐ {points} ball\n"
    await message.answer(text)

# ================= Barcha turlarni relay qilish (MEDIA + TEXT) =================
@dp.message_handler(content_types=types.ContentType.ANY)
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    # username/ism yangilab turamiz
    cur.execute("UPDATE users SET username=?, first_name=? WHERE user_id=?",
                (message.from_user.username or "", message.from_user.first_name or "", user_id))
    conn.commit()

    # faqat /buyruqlar emas, oddiy xabarlar
    if message.text and message.text.startswith('/'):
        return

    cur.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (user_id,))
    partner = cur.fetchone()
    if partner:
        partner_id = partner[0]
        try:
            # har qanday kontent turini ko'chirib yuboramiz
            await message.copy_to(partner_id)
        except Exception as e:
            await message.answer("⚠️ Xabarni yuborib bo‘lmadi.")
    else:
        await message.answer("⚠️ Siz hozir hech kim bilan suhbatda emassiz. /chat bosing.")

# 🚀 BOT ISHGA TUSHIRISH
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
