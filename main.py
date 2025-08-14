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
USERS = {}   # user_id : {'lang': None, 'chatting_with': None, 'vip': False, 'vip_until': None, 'refs': 0, 'name': None, 'age': None, 'gender': None, 'location': None}
QUEUE = []

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
            'name': None,
            'age': None,
            'gender': None,
            'location': None
        }

    # Referral orqali kirgan bo‘lsa
    if args and args[0].startswith("ref_"):
        inviter_id = int(args[0].split("_")[1])
        if inviter_id != user_id and inviter_id in USERS:
            USERS[inviter_id]['refs'] += 1
            # 10+ do‘st chaqirilsa VIP 7 kun
            if USERS[inviter_id]['refs'] >= 10 and not USERS[inviter_id]['vip']:
                USERS[inviter_id]['vip'] = True
                USERS[inviter_id]['vip_until'] = datetime.now() + timedelta(days=7)
                await context.bot.send_message(inviter_id, "🏆 Tabriklaymiz! Siz VIP bo‘ldingiz 7 kun davomida!")

    # Boshlang‘ich dizayn matni
    text = (
        "👋 **Chat360** ga xush kelibsiz!\n\n"
        "📌 Bu botda siz anonim ravishda istalgan odam bilan muloqot qilishingiz mumkin.\n"
        "🌐 Matn va audio yuborish imkoniyati mavjud.\n"
        "⚡ VIP navbat orqali suhbatdoshni tezroq topishingiz mumkin.\n"
        "👥 Do‘stlaringizni taklif qilib VIP oling!\n\n"
        f"🔗 Sizning referral linkingiz:\nhttps://t.me/{context.bot.username}?start=ref_{user_id}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    await update.message.reply_text("Tilni tanlang:", reply_markup=get_lang_keyboard())

async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = query.data
    USERS[user_id]['lang'] = lang
    await query.answer(f"Til tanlandi: {LANGUAGES[lang]}")
    await query.message.reply_text("💬 Suhbatni boshlash uchun /match buyrug‘ini bosing.")

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    check_vip(user_id)

    if user_id not in QUEUE:
        if USERS[user_id].get('vip'):
            QUEUE.insert(0, user_id)
        else:
            QUEUE.append(user_id)

    await update.message.reply_text("🔎 Suhbatdosh topilmoqda...")

    while len(QUEUE) >= 2:
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

# --- PROFILE HANDLER ---
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USERS:
        await update.message.reply_text("❗ Iltimos, avval /start buyrug‘i bilan botni ishga tushiring.")
        return

    args = context.args
    if len(args) < 4:
        await update.message.reply_text(
            "📝 Profilni to‘ldirish uchun:\n"
            "/profile Ism Yosh Jins Qayerdan\n\n"
            "Masalan:\n"
            "/profile Behruz 29 Erkak Sherobod"
        )
        return

    name, age, gender, location = args[0], args[1], args[2], " ".join(args[3:])
    USERS[user_id]['name'] = name
    USERS[user_id]['age'] = age
    USERS[user_id]['gender'] = gender
    USERS[user_id]['location'] = location

    await update.message.reply_text(
        f"✅ Profil yangilandi:\n"
        f"Ism: {name}\n"
        f"Yosh: {age}\n"
        f"Jins: {gender}\n"
        f"Qayerdan: {location}"
    )

# --- VIP STATUS HANDLER ---
async def vip_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    check_vip(user_id)
    user = USERS.get(user_id, {})
    if user.get('vip'):
        remaining = user['vip_until'] - datetime.now()
        days, remainder = divmod(remaining.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        status_text = f"💎 VIP foydalanuvchi\n⏳ Qolgan vaqt: {int(days)} kun {int(hours)} soat {int(minutes)} minut"
    else:
        status_text = "❌ Oddiy foydalanuvchi"
    refs = user.get('refs', 0)
    await update.message.reply_text(f"{status_text}\n👥 Taklif qilganlar: {refs}")

# --- ADMIN DATA ---
async def admin_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return

    text = "📊 RAMdagi ma'lumotlar:\n\n"
    for uid, info in USERS.items():
        vip = "✅" if info.get('vip') else "❌"
        vip_until = info.get('vip_until')
        vip_until_str = vip_until.strftime("%Y-%m-%d %H:%M") if vip_until else "N/A"
        text += (
            f"ID: {uid}\n"
            f"Ism: {info.get('name')}\n"
            f"Yosh: {info.get('age')}\n"
            f"Jins: {info.get('gender')}\n"
            f"Qayerdan: {info.get('location')}\n"
            f"Til: {info.get('lang')}\n"
            f"Chatting_with: {info.get('chatting_with')}\n"
            f"VIP: {vip} (Until: {vip_until_str})\n"
            f"Refs: {info.get('refs')}\n\n"
        )
    await update.message.reply_text(text)

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CommandHandler("vip", vip_status))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("admin_data", admin_data))
    app.add_handler(CallbackQueryHandler(lang_select, pattern='^(' + '|'.join(LANGUAGES.keys()) + ')$'))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(next|stop|report)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, audio_handler))

    print("✅ Bot ishga tushdi...")
    app.run_polling()
