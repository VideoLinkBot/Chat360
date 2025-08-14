# main.py
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# --- TOKEN VA ADMIN ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6905227976  # Adminga shikoyat yuborish uchun
if not BOT_TOKEN:
    raise ValueError("❌ Telegram bot tokeni topilmadi!")

# --- GLOBAL STATE ---
USERS = {}  # user_id: {'lang', 'profile': {'name','age','gender','province'}, 'profile_step', 'vip', 'vip_until', 'refs', 'chatting_with'}
QUEUE = []  # match navbati

LANGUAGES = {
    'uz': '🇺🇿 O‘zbekcha',
    'ru': '🇷🇺 Русский',
    'en': '🇬🇧 English'
}

PROVINCES = [
    'Toshkent', 'Samarqand', 'Buxoro', 'Farg‘ona', 'Andijon',
    'Surxondaryo', 'Qoraqalpog‘iston', 'Namangan', 'Jizzax',
    'Navoiy', 'Sirdaryo', 'Xorazm'
]

# ---------- Helperlar ----------
def kb_language() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(name, callback_data=f"lang:{code}")]
            for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(rows)

def kb_chat() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Keyingi", callback_data="chat:next")],
        [InlineKeyboardButton("⏹ To‘xtatish", callback_data="chat:stop")],
        [InlineKeyboardButton("🚫 Shikoyat", callback_data="chat:report")]
    ])

def kb_vip_status(user_id: int) -> InlineKeyboardMarkup:
    is_vip = USERS.get(user_id, {}).get('vip', False)
    txt = "VIP holati: ✅" if is_vip else "VIP holati: ❌"
    return InlineKeyboardMarkup([[InlineKeyboardButton(txt, callback_data="vip:status")]])

def is_profile_complete(user_id: int) -> bool:
    p = USERS[user_id].get('profile', {})
    return all(p.get(k) for k in ['name', 'age', 'gender', 'province'])

def check_vip_expiry(user_id: int):
    u = USERS.get(user_id)
    if not u:
        return
    until = u.get('vip_until')
    if u.get('vip') and until and datetime.now() > until:
        u['vip'] = False
        u['vip_until'] = None

def enqueue(user_id: int):
    # VIP ustunligi: VIP bo‘lsa, navbat boshiga qo‘yamiz; aks holda oxiriga.
    if user_id in QUEUE:
        return
    if USERS[user_id].get('vip'):
        QUEUE.insert(0, user_id)
    else:
        QUEUE.append(user_id)

def try_pair(context: ContextTypes.DEFAULT_TYPE):
    # Navbatdagi 2 foydalanuvchini ulash
    if len(QUEUE) < 2:
        return
    u1 = QUEUE.pop(0)
    u2 = QUEUE.pop(0)
    USERS[u1]['chatting_with'] = u2
    USERS[u2]['chatting_with'] = u1
    # Ikkalasiga ham tugmalar bilan xabar
    return u1, u2

def normalize_gender(text: str) -> str:
    t = text.strip().lower()
    # Erkak variantlari
    if t in ["erkak", "o'g'il", "ogil", "boy", "male", "m"]:
        return "Erkak"
    # Ayol variantlari
    if t in ["ayol", "qiz", "girl", "female", "f"]:
        return "Ayol"
    # Aks holda foydalanuvchi yozganini saqlaymiz
    return text.strip()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    user_id = user.id

    # USER init
    if user_id not in USERS:
        USERS[user_id] = {
            'lang': None,
            'profile': {'name': None, 'age': None, 'gender': None, 'province': None},
            'profile_step': None,
            'vip': False,
            'vip_until': None,
            'refs': 0,
            'chatting_with': None
        }

    # Referral (t.me/YourBot?start=ref_<id>)
    args = context.args
    if args and args[0].startswith("ref_"):
        inviter_id_str = args[0].split("_", 1)[1]
        if inviter_id_str.isdigit():
            inviter_id = int(inviter_id_str)
            if inviter_id != user_id and inviter_id in USERS:
                USERS[inviter_id]['refs'] += 1
                # 10 referal = 7 kun VIP
                if USERS[inviter_id]['refs'] >= 10 and not USERS[inviter_id]['vip']:
                    USERS[inviter_id]['vip'] = True
                    USERS[inviter_id]['vip_until'] = datetime.now() + timedelta(days=7)
                    await context.bot.send_message(
                        inviter_id,
                        "🏆 Tabriklaymiz! 10 ta do‘st chaqirdingiz va 7 kun VIP oldingiz!"
                    )

    # Boshlang‘ich dizayn + til tanlash
    intro = (
        "👋 **Chat360** ga xush kelibsiz!\n\n"
        "📌 Bu botda siz anonim ravishda istalgan odam bilan muloqot qilishingiz mumkin.\n"
        "🌐 Matn yuboring — hammasi shunchaki.\n"
        "⚡ VIP navbat orqali suhbatdoshni tezroq topishingiz mumkin.\n"
        "👥 10 ta do‘st chaqiring — 7 kun VIP!\n\n"
        f"🔗 Sizning referral linkingiz:\n"
        f"https://t.me/{context.bot.username}?start=ref_{user_id}\n\n"
        "Iltimos, **tilni tanlang**:"
    )
    await context.bot.send_message(chat.id, intro, parse_mode="Markdown", reply_markup=kb_language())

# ---------- LANGUAGE CALLBACK ----------
async def on_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    _, code = query.data.split(":", 1)  # lang:uz
    if code not in LANGUAGES:
        await query.answer("Noto‘g‘ri tanlov.")
        return
    USERS[user_id]['lang'] = code
    await query.answer(f"Til: {LANGUAGES[code]}")

    # Til tanlangach — profilni matn bilan so‘raymiz (tugmalarsiz)
    USERS[user_id]['profile_step'] = 'name'
    await query.message.reply_text("Ismingizni kiriting:")
    # VIP holatini ham ko‘rsatib qo‘yamiz
    await query.message.reply_text("VIP bo‘limi:", reply_markup=kb_vip_status(user_id))

# ---------- VIP CALLBACK ----------
async def on_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    check_vip_expiry(user_id)
    is_vip = USERS[user_id].get('vip', False)
    until = USERS[user_id].get('vip_until')
    if is_vip and until:
        left = until - datetime.now()
        days = max(0, left.days)
        hours = max(0, int((left.seconds) / 3600))
        text = f"💎 VIP: ✅\n⏳ Qolgan vaqt: {days} kun {hours} soat"
    else:
        text = "💎 VIP: ❌\n10 ta do‘st chaqirsangiz 7 kun VIP beriladi."
    await query.answer("VIP holati")
    await query.message.reply_text(text)

# ---------- PROFILE (MATN BILAN) ----------
async def profile_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    # Agar chatda bo‘lsa — yozilgan matnni juftiga yuboramiz
    partner = USERS.get(user_id, {}).get('chatting_with')
    if partner:
        # Oddiy relay
        await context.bot.send_message(partner, text)
        return

    # Profil bosqichi bo‘lmasa — hech bo‘lmaganda boshlatamiz
    if user_id not in USERS:
        USERS[user_id] = {
            'lang': None,
            'profile': {'name': None, 'age': None, 'gender': None, 'province': None},
            'profile_step': 'name',
            'vip': False,
            'vip_until': None,
            'refs': 0,
            'chatting_with': None
        }

    step = USERS[user_id].get('profile_step')

    # Agar til tanlanmagan bo‘lsa, foydalanuvchini /start ga yo‘naltiramiz
    if USERS[user_id].get('lang') is None:
        await update.message.reply_text("Iltimos, avval /start bosib tilni tanlang.")
        return

    # Bosqichma-bosqich qabul qilish
    if step == 'name' or step is None:
        USERS[user_id]['profile']['name'] = text
        USERS[user_id]['profile_step'] = 'age'
        await update.message.reply_text("Yoshingizni kiriting (masalan: 23):")
        return

    if step == 'age':
        # Yoshi oddiy tekshiruv
        if not text.isdigit() or not (7 <= int(text) <= 100):
            await update.message.reply_text("Yosh noto‘g‘ri. Iltimos, faqat son kiriting (masalan: 23).")
            return
        USERS[user_id]['profile']['age'] = text
        USERS[user_id]['profile_step'] = 'gender'
        await update.message.reply_text("Jinsingizni kiriting (Erkak/Ayol):")
        return

    if step == 'gender':
        USERS[user_id]['profile']['gender'] = normalize_gender(text)
        USERS[user_id]['profile_step'] = 'province'
        await update.message.reply_text("Qayerdansiz? (Viloyat yoki shahar, masalan: Toshkent)")
        return

    if step == 'province':
        USERS[user_id]['profile']['province'] = text
        USERS[user_id]['profile_step'] = None

        # Tekshiruv va yakuniy xabar
        p = USERS[user_id]['profile']
        summ = (
            "✅ Profil saqlandi!\n"
            f"• Ism: {p['name']}\n"
            f"• Yosh: {p['age']}\n"
            f"• Jins: {p['gender']}\n"
            f"• Hudud: {p['province']}\n\n"
            "Endi suhbatni boshlash uchun /match buyrug‘ini bosing."
        )
        await update.message.reply_text(summ)
        return

    # Agar hammasi to‘liq bo‘lsa, foydalanuvchiga ko‘rsatamiz
    if is_profile_complete(user_id):
        await update.message.reply_text("Profil allaqachon to‘ldirilgan. Suhbatni boshlash uchun /match yuboring.")
    else:
        # Noaniq holat bo‘lsa, qayta boshlatamiz
        USERS[user_id]['profile_step'] = 'name'
        await update.message.reply_text("Keling, qaytadan boshlaymiz. Ismingizni kiriting:")

# ---------- /vip ----------
async def cmd_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    check_vip_expiry(user_id)
    u = USERS.get(user_id)
    if not u:
        await update.message.reply_text("Avval /start bosing.")
        return
    is_vip = u.get('vip', False)
    until = u.get('vip_until')
    if is_vip and until:
        left = until - datetime.now()
        days = max(0, left.days)
        hours = max(0, int(left.seconds / 3600))
        txt = f"💎 VIP: ✅\n⏳ Qolgan vaqt: {days} kun {hours} soat"
    else:
        txt = "💎 VIP: ❌\n10 ta do‘st chaqirsangiz avtomatik 7 kun VIP bo‘lasiz."
    await update.message.reply_text(txt, reply_markup=kb_vip_status(user_id))

# ---------- /referral ----------
async def cmd_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    refs = USERS.get(user_id, {}).get('refs', 0)
    await update.message.reply_text(
        f"🔗 Referral link: {link}\n👥 Siz hozirgacha {refs} do‘st chaqirdingiz.\n"
        "10 ta do‘st = 7 kun VIP!"
    )

# ---------- /match ----------
async def cmd_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Profil to‘liq bo‘lmasa — to‘ldirishni so‘raymiz
    if user_id not in USERS or not is_profile_complete(user_id):
        USERS.setdefault(user_id, {})  # safety
        USERS[user_id]['profile_step'] = USERS[user_id].get('profile_step') or 'name'
        await update.message.reply_text("Avval profilingizni to‘ldiring. Ismingizni kiriting:")
        return

    # Agar allaqachon chatda bo‘lsa
    if USERS[user_id].get('chatting_with'):
        await update.message.reply_text("Siz hozir suhbatdasiz. Tugmalar orqali boshqaring.", reply_markup=kb_chat())
        return

    # Navbatga qo‘shish
    check_vip_expiry(user_id)
    enqueue(user_id)
    await update.message.reply_text("🔎 Suhbatdosh qidirilmoqda...")

    # Juftlashishga urinish
    paired = try_pair(context)
    if paired:
        u1, u2 = paired
        await context.bot.send_message(u1, "🆕 Suhbatdosh topildi! Xabar yozing.", reply_markup=kb_chat())
        await context.bot.send_message(u2, "🆕 Suhbatdosh topildi! Xabar yozing.", reply_markup=kb_chat())

# ---------- Chatdagi matn relay ----------
async def chat_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Agar foydalanuvchi chatda bo‘lsa — matnini juftiga uzatamiz.
       Aks holda bu handler ishlamaydi (profil handleri ishlaydi)."""
    user_id = update.effective_user.id
    partner = USERS.get(user_id, {}).get('chatting_with')
    if not partner:
        return  # Profil handler bu xabarni ushlaydi
    txt = update.message.text
    if not txt:
        return
    await context.bot.send_message(partner, txt)

# ---------- Chat tugmalari ----------
async def on_chat_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data  # chat:next / chat:stop / chat:report
    partner = USERS.get(user_id, {}).get('chatting_with')

    if data == "chat:next":
        # Joriy chatni tozalaymiz
        if partner:
            USERS[partner]['chatting_with'] = None
            await context.bot.send_message(partner, "🔄 Suhbatdoshingiz keyingisini tanladi. /match bosing.")
        USERS[user_id]['chatting_with'] = None
        # Yangi match
        await query.message.reply_text("🔎 Yangi suhbatdosh qidirilmoqda...")
        check_vip_expiry(user_id)
        enqueue(user_id)
        paired = try_pair(context)
        if paired:
            u1, u2 = paired
            await context.bot.send_message(u1, "🆕 Suhbatdosh topildi! Xabar yozing.", reply_markup=kb_chat())
            await context.bot.send_message(u2, "🆕 Suhbatdosh topildi! Xabar yozing.", reply_markup=kb_chat())
        else:
            await query.message.reply_text("⏳ Hozircha topilmadi, birozdan so‘ng avtomatik ulanadi.")
        await query.answer("Keyingisi...")
        return

    if data == "chat:stop":
        if partner:
            USERS[partner]['chatting_with'] = None
            await context.bot.send_message(partner, "⏹ Suhbat tugadi. /match bilan yangi suhbat boshlang.")
        USERS[user_id]['chatting_with'] = None
        await query.message.reply_text("⏹ Suhbat tugadi.")
        await query.answer("To‘xtatildi")
        return

    if data == "chat:report":
        # Adminga shikoyat
        await query.answer("Shikoyatingiz yuborildi.")
        await query.message.reply_text("✅ Rahmat! Shikoyat adminga yuborildi.")
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"🚫 Shikoyat: reporter={user_id}, partner={partner}"
            )
        except Exception:
            pass
        return

# ---------- ADMIN: /admin_data (ixtiyoriy) ----------
async def cmd_admin_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz.")
        return
    lines = ["📊 Hozirgi foydalanuvchilar:"]
    for uid, info in USERS.items():
        vip = "✅" if info.get('vip') else "❌"
        vu = info.get('vip_until')
        vu_str = vu.strftime("%Y-%m-%d %H:%M") if vu else "—"
        p = info.get('profile', {})
        lines.append(
            f"ID:{uid} | VIP:{vip} (gacha: {vu_str}) | Refs:{info.get('refs',0)} | "
            f"Lang:{info.get('lang')} | ChatWith:{info.get('chatting_with')} | "
            f"Ism:{p.get('name')} Yosh:{p.get('age')} Jins:{p.get('gender')} Hudud:{p.get('province')}"
        )
    await update.message.reply_text("\n".join(lines[:1000]))

# ---------- APP ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("vip", cmd_vip))
    app.add_handler(CommandHandler("match", cmd_match))
    app.add_handler(CommandHandler("referral", cmd_referral))
    app.add_handler(CommandHandler("admin_data", cmd_admin_data))

    # Callbacklar
    app.add_handler(CallbackQueryHandler(on_language, pattern=r"^lang:"))
    app.add_handler(CallbackQueryHandler(on_vip, pattern=r"^vip:"))
    app.add_handler(CallbackQueryHandler(on_chat_buttons, pattern=r"^chat:"))

    # Matn:
    # 1) agar foydalanuvchi chatda bo‘lsa — chat_text_router relay qiladi
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_text_router))
    # 2) aks holda — profile_text profilni to‘ldiradi
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_text))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
