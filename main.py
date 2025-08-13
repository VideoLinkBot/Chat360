# main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

# --- GLOBALS ---
USERS = {}   # user_id : {'lang': 'uz', 'chatting_with': None}
QUEUE = []   # navbatdagi foydalanuvchilar

LANGUAGES = {
    'uz': '🇺🇿 O‘zbekcha',
    'ru': '🇷🇺 Ruscha',
    'en': '🇬🇧 Inglizcha',
    'ko': '🇰🇷 Koreyscha'
}

# --- HELPERS ---
def get_lang_keyboard():
    keyboard = [[InlineKeyboardButton(name, callback_data=code)] for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(keyboard)

def get_chat_buttons():
    keyboard = [
        [InlineKeyboardButton("🔄 Keyingi", callback_data='next')],
        [InlineKeyboardButton("⏹ To‘xtatish", callback_data='stop')],
        [InlineKeyboardButton("🚫 Shikoyat", callback_data='report')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USERS[user_id] = {'lang': None, 'chatting_with': None}
    await update.message.reply_text(
        "🤖 Salom! Tilni tanlang:",
        reply_markup=get_lang_keyboard()
    )

async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = query.data
    USERS[user_id]['lang'] = lang
    await query.answer(f"Til tanlandi: {LANGUAGES[lang]}")
    await query.message.reply_text(
        "💬 Suhbatni boshlash uchun /match buyrug‘ini bosing."
    )

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in QUEUE:
        QUEUE.append(user_id)
    await update.message.reply_text("🔎 Suhbatdosh topilmoqda...")
    
    # Agar navbatda boshqa foydalanuvchi bo‘lsa
    if len(QUEUE) >= 2:
        u1 = QUEUE.pop(0)
        u2 = QUEUE.pop(0)
        USERS[u1]['chatting_with'] = u2
        USERS[u2]['chatting_with'] = u1
        
        for uid in [u1, u2]:
            await context.bot.send_message(
                chat_id=uid,
                text="🆕 Suhbatdosh topildi! Matn yozing yoki audio yuboring 🎙",
                reply_markup=get_chat_buttons()
            )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USERS or USERS[user_id]['chatting_with'] is None:
        await update.message.reply_text("❗ Suhbatdosh topilmagan. /match buyrug‘ini bosing.")
        return
    
    partner_id = USERS[user_id]['chatting_with']
    user_lang = USERS[user_id]['lang']
    partner_lang = USERS[partner_id]['lang']
    
    text = update.message.text
    if user_lang != partner_lang:
        try:
            text = GoogleTranslator(source=user_lang, target=partner_lang).translate(text)
        except Exception:
            pass
    
    await context.bot.send_message(chat_id=partner_id, text=text)

async def audio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USERS or USERS[user_id]['chatting_with'] is None:
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
    app = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CallbackQueryHandler(lang_select, pattern='^(' + '|'.join(LANGUAGES.keys()) + ')$'))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(next|stop|report)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, audio_handler))
    
    print("Bot ishga tushdi...")
    app.run_polling()
