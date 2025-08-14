# main.py
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- TOKEN VA ADMIN ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6905227976
if not BOT_TOKEN:
    raise ValueError("❌ Telegram bot tokeni topilmadi!")

# --- GLOBALS ---
USERS = {}
QUEUE = []

LANGUAGES = {
    'uz': '🇺🇿 O‘zbekcha',
    'ru': '🇷🇺 Ruscha',
    'en': '🇬🇧 Inglizcha',
    'ko': '🇰🇷 Koreyscha'
}

GENDERS = ['Erkak', 'Ayol']
AGES = ['15-20', '21-30', '31-40', '41+']
PROVINCES = [
    'Toshkent', 'Samarqand', 'Buxoro', 'Farg‘ona', 'Andijon',
    'Surxondaryo', 'Qoraqalpog‘iston', 'Namangan', 'Jizzax',
    'Navoiy', 'Sirdaryo', 'Xorazm'
]

# --- HELPERS ---
def get_lang_keyboard():
    keyboard = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")] for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(keyboard)

def get_gender_keyboard():
    keyboard = [[InlineKeyboardButton(g, callback_data=f"gender_{g}")] for g in GENDERS]
    return InlineKeyboardMarkup(keyboard)

def get_age_keyboard():
    keyboard = [[InlineKeyboardButton(a, callback_data=f"age_{a}")] for a in AGES]
    return InlineKeyboardMarkup(keyboard)

def get_province_keyboard():
    keyboard = [[InlineKeyboardButton(p, callback_data=f"province_{p}")] for p in PROVINCES]
    return InlineKeyboardMarkup(keyboard)

def get_chat_buttons():
    keyboard = [
        [InlineKeyboardButton("🔄 Keyingi", callback_data='next')],
        [InlineKeyboardButton("⏹ To‘xtatish", callback_data='stop')],
        [InlineKeyboardButton("🚫 Shikoyat", callback_data='report')]
    ]
    return InlineKeyboardMarkup(keyboard)

def check_vip(user_id):
    user = USERS.get(user_id)
    if user and user.get('vip') and user.get('vip_until'):
        if datetime.now() > user['vip_until']:
            user['vip'] = False
            user['vip_until'] = None

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Suhbatdosh topish (VIP avval, filtrlar bo‘yicha)"""
    user_id = update.effective_user.id
    user = USERS[user_id]
    check_vip(user_id)

    # Filtrlash: jins, yosh, viloyat
    candidates = []
    for uid, u in USERS.items():
        if uid == user_id:
            continue
        if u.get('chatting_with'):
            continue
        # Filtrlar
        if u['profile'].get('gender') != user['profile'].get('gender') and user['profile'].get('gender') != 'Hammasi':
            continue
        if u['profile'].get('age') != user['profile'].get('age') and user['profile'].get('age') != 'Hammasi':
            continue
        if u['profile'].get('province') != user['profile'].get('province') and user['profile'].get('province') != 'Hammasi':
            continue
        candidates.append(uid)

    # VIP birinchi
    vip_candidates = [uid for uid in candidates if USERS[uid].get('vip')]
    selected = None
    if user.get('vip') and vip_candidates:
        selected = vip_candidates[0]
    elif candidates:
        selected = candidates[0]

    if selected:
        USERS[user_id]['chatting_with'] = selected
        USERS[selected]['chatting_with'] = user_id
        await context.bot.send_message(chat_id=user_id, text="✅ Suhbat boshlandi!", reply_markup=get_chat_buttons())
        await context.bot.send_message(chat_id=selected, text="✅ Suhbat boshlandi!", reply_markup=get_chat_buttons())
    else:
        QUEUE.append(user_id)
        await context.bot.send_message(chat_id=user_id, text="🔄 Suhbatdosh topilmadi, biroz kuting...")

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if user_id not in USERS:
        USERS[user_id] = {
            'lang': None,
            'chatting_with': None,
            'vip': False,
            'vip_until': None,
            'refs': 0,
            'profile': {}
        }

    # Referral
    if args and args[0].startswith("ref_"):
        inviter_id = int(args[0].split("_")[1])
        if inviter_id != user_id and inviter_id in USERS:
            USERS[inviter_id]['refs'] += 1
            if USERS[inviter_id]['refs'] >= 10 and not USERS[inviter_id]['vip']:
                USERS[inviter_id]['vip'] = True
                USERS[inviter_id]['vip_until'] = datetime.now() + timedelta(days=7)
                await context.bot.send_message(inviter_id, "🏆 Tabriklaymiz! Siz VIP bo‘ldingiz 7 kun davomida!")

    await update.message.reply_text("👋 Salom! Iltimos, ismingizni kiriting:")

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if 'name' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['name'] = text
        await update.message.reply_text("Yoshingizni tanlang:", reply_markup=get_age_keyboard())
    elif 'age' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['age'] = text
        await update.message.reply_text("Jinsingizni tanlang:", reply_markup=get_gender_keyboard())
    elif 'gender' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['gender'] = text
        await update.message.reply_text("Qayerdansiz?", reply_markup=get_province_keyboard())
    elif 'province' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['province'] = text

        # Boshlang‘ich dizayn
        text_intro = (
            "👋 **Chat360** ga xush kelibsiz!\n\n"
            "📌 Bu botda siz anonim ravishda istalgan odam bilan muloqot qilishingiz mumkin.\n"
            "🌐 Matn va audio yuborish imkoniyati mavjud.\n"
            "⚡ VIP navbat orqali suhbatdoshni tezroq topishingiz mumkin.\n"
            "👥 Do‘stlaringizni taklif qilib VIP oling!\n\n"
            f"🔗 Sizning referral linkingiz:\nhttps://t.me/{context.bot.username}?start=ref_{user_id}"
        )
        await update.message.reply_text(text_intro, parse_mode="Markdown")
        await update.message.reply_text("Tilni tanlang:", reply_markup=get_lang_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("lang_"):
        USERS[user_id]['lang'] = data.split("_")[1]
        await query.answer(f"Til tanlandi: {LANGUAGES[USERS[user_id]['lang']]}")
        await query.message.reply_text("💬 Suhbatni boshlash uchun /match buyrug‘ini bosing.")
        return
    elif data.startswith("gender_"):
        USERS[user_id]['profile']['gender'] = data.split("_")[1]
        await query.answer(f"Jins tanlandi: {USERS[user_id]['profile']['gender']}")
        await query.message.reply_text("Qayerdansiz?", reply_markup=get_province_keyboard())
        return
    elif data.startswith("age_"):
        USERS[user_id]['profile']['age'] = data.split("_")[1]
        await query.answer(f"Yosh oralig‘i tanlandi: {USERS[user_id]['profile']['age']}")
        return
    elif data.startswith("province_"):
        USERS[user_id]['profile']['province'] = data.split("_")[1]
        await query.answer(f"Viloyat tanlandi: {USERS[user_id]['profile']['province']}")
        await query.message.reply_text("Endi /match buyrug‘i bilan suhbatni boshlashingiz mumkin.")
        return

    # Chat tugmalari
    partner_id = USERS[user_id]['chatting_with']
    if data == 'next':
        if partner_id:
            USERS[partner_id]['chatting_with'] = None
        USERS[user_id]['chatting_with'] = None
        await query.message.reply_text("🔄 Keyingi suhbatdosh topilmoqda...")
        await match(update, context)
    elif data == 'stop':
        if partner_id:
            USERS[partner_id]['chatting_with'] = None
            await context.bot.send_message(chat_id=partner_id, text="⏹ Suhbat tugadi.")
        USERS[user_id]['chatting_with'] = None
        await query.message.reply_text("⏹ Suhbat tugadi.")
    elif data == 'report':
        await query.message.reply_text("✅ Rahmat! Suhbat boshqaruvchiga yuborildi.")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = USERS.get(user_id, {}).get('chatting_with')
    if partner_id:
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)

async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = USERS.get(user_id, {}).get('chatting_with')
    if partner_id:
        await context.bot.send_audio(chat_id=partner_id, audio=update.message.audio.file_id)

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("match", match))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.AUDIO, audio_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot ishga tushdi...")
    app.run_polling()
