# main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# --- TOKEN ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Telegram bot tokeni topilmadi! Environment Variable qo‘shilganligini tekshiring.")

# --- STATES ---
NAME, AGE, GENDER, LOCATION, LANGUAGE = range(5)

# --- DATA ---
USERS = {}   # user_id : user_data
QUEUE = []

LANGUAGES = {
    'uz': '🇺🇿 O‘zbekcha',
    'ru': '🇷🇺 Ruscha',
    'en': '🇬🇧 Inglizcha',
    'ko': '🇰🇷 Koreyscha'
}

GENDERS = {
    'male': '👨 Erkak',
    'female': '👩 Ayol'
}

# --- HELPERS ---
def get_lang_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(name, callback_data=code)] for code, name in LANGUAGES.items()])

def get_gender_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(name, callback_data=code)] for code, name in GENDERS.items()])

def get_chat_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Keyingi", callback_data='next')],
        [InlineKeyboardButton("⏹ To‘xtatish", callback_data='stop')],
        [InlineKeyboardButton("🚫 Shikoyat", callback_data='report')]
    ])

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Chat360 Bot* — bu anonim chat platformasi.\n\n"
        "✅ Siz anonim ravishda boshqa foydalanuvchilar bilan suhbatlasha olasiz.\n"
        "✅ Til tanlashingiz va tarjima funksiyasidan foydalanishingiz mumkin.\n"
        "✅ Audio va matnli xabarlarni yuborish imkoni bor.\n\n"
        "Keling, ro‘yxatdan o‘tamiz. Ismingizni kiriting:",
        parse_mode="Markdown"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS[user_id] = {"name": update.message.text}
    await update.message.reply_text("📅 Yosh kiriting:")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS[user_id]["age"] = update.message.text
    await update.message.reply_text("⚧ Jinsingizni tanlang:", reply_markup=get_gender_keyboard())
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    USERS[user_id]["gender"] = query.data
    await query.answer()
    await query.message.reply_text("📍 Qayerdansiz (shahar yoki mamlakat kiriting):")
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS[user_id]["location"] = update.message.text
    await update.message.reply_text("🌐 Tilni tanlang:", reply_markup=get_lang_keyboard())
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    USERS[user_id]["lang"] = query.data
    await query.answer()
    await query.message.reply_text(
        "✅ Ro‘yxatdan o‘tish yakunlandi!\n"
        "💬 Suhbatni boshlash uchun /match buyrug‘ini bosing."
    )
    return ConversationHandler.END

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in QUEUE:
        QUEUE.append(user_id)
    await update.message.reply_text("🔎 Suhbatdosh topilmoqda...")

    if len(QUEUE) >= 2:
        u1 = QUEUE.pop(0)
        u2 = QUEUE.pop(0)
        USERS[u1]['chatting_with'] = u2
        USERS[u2]['chatting_with'] = u1

        for uid in [u1, u2]:
            await context.bot.send_message(
                chat_id=uid,
                text=f"🆕 Suhbatdosh topildi!\n"
                     f"👤 {USERS[uid]['name']}, {USERS[uid]['age']} yosh, {GENDERS[USERS[uid]['gender']]}, {USERS[uid]['location']}",
                reply_markup=get_chat_buttons()
            )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if 'chatting_with' not in USERS.get(user_id, {}) or USERS[user_id]['chatting_with'] is None:
        await update.message.reply_text("❗ Suhbatdosh topilmagan. /match buyrug‘ini bosing.")
        return

    partner_id = USERS[user_id]['chatting_with']
    await context.bot.send_message(chat_id=partner_id, text=update.message.text)

async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if 'chatting_with' not in USERS.get(user_id, {}) or USERS[user_id]['chatting_with'] is None:
        await update.message.reply_text("❗ Suhbatdosh topilmagan. /match buyrug‘ini bosing.")
        return

    partner_id = USERS[user_id]['chatting_with']
    audio_file = update.message.voice or update.message.audio
    if audio_file:
        file = await context.bot.get_file(audio_file.file_id)
        filename = f"{audio_file.file_id}.ogg"
        await file.download_to_drive(filename)
        await context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.RECORD_VOICE)
        with open(filename, 'rb') as f:
            await context.bot.send_voice(chat_id=partner_id, voice=f)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    partner_id = USERS[user_id].get('chatting_with')

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
        await query.message.reply_text("✅ Rahmat! Shikoyatingiz qabul qilindi.")

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [CallbackQueryHandler(get_gender, pattern='^(male|female)$')],
            LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            LANGUAGE: [CallbackQueryHandler(set_language, pattern='^(' + '|'.join(LANGUAGES.keys()) + ')$')]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(next|stop|report)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, audio_handler))

    print("✅ Bot ishga tushdi...")
    app.run_polling()
