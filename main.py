        # main.py
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random

# --- TOKEN VA ADMIN ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6905227976
if not BOT_TOKEN:
    raise ValueError("❌ Telegram bot tokeni topilmadi!")

# --- GLOBALS ---
USERS = {}

LANGUAGES = {
    'uz': '🇺🇿 O‘zbekcha',
    'ru': '🇷🇺 Ruscha',
    'en': '🇬🇧 Inglizcha',
    'ko': '🇰🇷 Koreyscha'
}

PROVINCES = [
    'Toshkent', 'Samarqand', 'Buxoro', 'Farg‘ona', 'Andijon',
    'Surxondaryo', 'Qoraqalpog‘iston', 'Namangan', 'Jizzax',
    'Navoiy', 'Sirdaryo', 'Xorazm'
]

# --- HELPERS ---
def get_lang_keyboard():
    keyboard = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")] for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(keyboard)

def get_vip_keyboard(user_id):
    user = USERS.get(user_id, {})
    vip = user.get('vip', False)
    text = "💎 Siz VIP foydalanuvchisiz" if vip else "❌ Oddiy foydalanuvchi"
    keyboard = [[InlineKeyboardButton(text, callback_data="vip_status")]]
    return InlineKeyboardMarkup(keyboard)

def check_vip(user_id):
    user = USERS.get(user_id)
    if user:
        if user.get('refs',0) >= 10 and not user.get('vip', False):
            user['vip'] = True
            user['vip_until'] = datetime.now() + timedelta(days=7)

def get_chat_buttons():
    keyboard = [
        [InlineKeyboardButton("🔄 Keyingi", callback_data='next')],
        [InlineKeyboardButton("⏹ To‘xtatish", callback_data='stop')],
        [InlineKeyboardButton("🚫 Shikoyat", callback_data='report')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- START ---
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
            check_vip(inviter_id)
            if USERS[inviter_id].get('vip', False):
                await context.bot.send_message(inviter_id, "🏆 Tabriklaymiz! Siz VIP bo‘ldingiz 7 kun davomida!")

    # Boshlang‘ich dizayn
    text_intro = (
        "👋 **Chat360** ga xush kelibsiz!\n\n"
        "📌 Bu botda siz anonim ravishda istalgan odam bilan muloqot qilishingiz mumkin.\n"
        "🌐 Matn va audio yuborish imkoniyati mavjud.\n"
        "⚡ VIP navbat orqali suhbatdoshni tezroq topishingiz mumkin.\n"
        "👥 Do‘stlaringizni taklif qilib VIP oling!"
    )
    await update.message.reply_text(text_intro, parse_mode="Markdown")
    await update.message.reply_text("Tilni tanlang:", reply_markup=get_lang_keyboard())

# --- INLINE BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("lang_"):
        USERS[user_id]['lang'] = data.split("_")[1]
        await query.answer(f"Til tanlandi: {USERS[user_id]['lang']}")
        await query.message.reply_text("Iltimos, ismingizni kiriting:")

    elif data == "vip_status":
        await query.answer("VIP holatingiz")
        await query.message.reply_text("Sizning VIP holatingizni tekshirish:", reply_markup=get_vip_keyboard(user_id))

    elif data == 'next':
        await query.answer("Keyingi suhbatdosh topilmoqda...")
        await match(update, context)
    elif data == 'stop':
        partner_id = USERS[user_id].get('chatting_with')
        if partner_id:
            USERS[partner_id]['chatting_with'] = None
        USERS[user_id]['chatting_with'] = None
        await query.message.reply_text("⏹ Suhbat tugadi.")
    elif data == 'report':
        await query.message.reply_text("✅ Rahmat! Suhbat boshqaruvchiga yuborildi.")

# --- PROFILE HANDLER ---
async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    profile = USERS[user_id]['profile']

    if 'name' not in profile:
        profile['name'] = text
        await update.message.reply_text("Yoshingizni kiriting:")
    elif 'age' not in profile:
        profile['age'] = text
        await update.message.reply_text("Jinsingizni kiriting (Erkak yoki Ayol):")
    elif 'gender' not in profile:
        profile['gender'] = text
        await update.message.reply_text("Qayerdansiz?")
    elif 'province' not in profile:
        profile['province'] = text
        check_vip(user_id)
        await update.message.reply_text(
            f"✅ Profil to‘ldirildi:\nIsm: {profile['name']}\nYosh: {profile['age']}\nJins: {profile['gender']}\nViloyat: {profile['province']}",
            reply_markup=get_vip_keyboard(user_id)
        )
        await update.message.reply_text("Endi /match buyrug‘i bilan suhbatni boshlashingiz mumkin.")

# --- MATCH FUNCTION ---
async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USERS[user_id]['chatting_with']:
        await update.message.reply_text("Siz allaqachon kimdir bilan suhbatdasiz.", reply_markup=get_chat_buttons())
        return

    available_users = [uid for uid, u in USERS.items() if uid != user_id and not u.get('chatting_with')]
    if not available_users:
        await update.message.reply_text("Hozircha boshqa foydalanuvchilar yo‘q, keyinroq urinib ko‘ring.")
        return

    partner_id = random.choice(available_users)
    USERS[user_id]['chatting_with'] = partner_id
    USERS[partner_id]['chatting_with'] = user_id
    await update.message.reply_text("✅ Suhbat boshlandi!", reply_markup=get_chat_buttons())
    await context.bot.send_message(partner_id, "✅ Suhbat boshlandi!", reply_markup=get_chat_buttons())

# --- MESSAGE FORWARDING ---
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = USERS[user_id].get('chatting_with')
    if partner_id:
        await context.bot.send_message(partner_id, update.message.text)

# --- MAIN ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    print("✅ Bot ishga tushdi...")
    app.run_polling()
