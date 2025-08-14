# main.py
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

# --- TOKEN VA ADMIN ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6905227976  # Sizning Telegram IDingiz
if not BOT_TOKEN:
    raise ValueError("❌ Telegram bot tokeni topilmadi!")

# --- GLOBALS ---
USERS = {}   # user_id : {'lang': None, 'chatting_with': None, 'vip': False, 'vip_until': None, 'refs': 0, 'profile': {}}
QUEUE = []

LANGUAGES = {
    'uz': '🇺🇿 O‘zbekcha',
    'ru': '🇷🇺 Ruscha',
    'en': '🇬🇧 Inglizcha',
    'ko': '🇰🇷 Koreyscha'
}

GENDERS = ['Erkak', 'Ayol']
AGES = ['15-20', '21-30', '31-40', '41+']
PROVINCES = ['Toshkent', 'Samarqand', 'Buxoro', 'Farg‘ona', 'Andijon', 'Surxondaryo', 'Qoraqalpog‘iston']

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
    """VIP muddati tugaganini tekshiradi"""
    user = USERS.get(user_id)
    if user and user.get('vip') and user.get('vip_until'):
        if datetime.now() > user['vip_until']:
            user['vip'] = False
            user['vip_until'] = None

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

    # Referral orqali kirgan bo‘lsa
    if args and args[0].startswith("ref_"):
        inviter_id = int(args[0].split("_")[1])
        if inviter_id != user_id and inviter_id in USERS:
            USERS[inviter_id]['refs'] += 1
            if USERS[inviter_id]['refs'] >= 10 and not USERS[inviter_id]['vip']:
                USERS[inviter_id]['vip'] = True
                USERS[inviter_id]['vip_until'] = datetime.now() + timedelta(days=7)
                await context.bot.send_message(inviter_id, "🏆 Tabriklaymiz! Siz VIP bo‘ldingiz 7 kun davomida!")

    # Profil ma’lumotlarini so‘rash
    await update.message.reply_text("Iltimos, ismingizni kiriting:")
    return

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if 'name' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['name'] = text
        await update.message.reply_text("Yoshingizni kiriting:")
    elif 'age' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['age'] = text
        await update.message.reply_text("Jinsingizni tanlang:", reply_markup=get_gender_keyboard())
    elif 'gender' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['gender'] = text
        await update.message.reply_text("Qayerdansiz?", reply_markup=get_province_keyboard())
    elif 'province' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['province'] = text

        # Boshlang‘ich dizayn chiqarish
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

# --- Til va boshqa tugmalar callback ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    # Profil tugmalari
    if data.startswith("lang_"):
        lang = data.split("_")[1]
        USERS[user_id]['lang'] = lang
        await query.answer(f"Til tanlandi: {LANGUAGES[lang]}")
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

    # Suhbat tugmalari
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

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    # Shu yerga avvalgi match, message_handler, audio_handler va vip_status handlerlarini qo‘shasiz

    print("✅ Bot ishga tushdi...")
    app.run_polling()
