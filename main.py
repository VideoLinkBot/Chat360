# main.py
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from deep_translator import GoogleTranslator

# --- TOKEN VA ADMIN ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 6905227976
if not BOT_TOKEN:
    raise ValueError("❌ Telegram bot tokeni topilmadi!")

# --- GLOBALS ---
USERS = {}  # user_id: {'lang': None, 'chatting_with': None, 'vip': False, 'vip_until': None, 'refs': 0, 'profile': {}}
QUEUE = []

LANGUAGES = {'uz':'🇺🇿 O‘zbekcha', 'ru':'🇷🇺 Ruscha', 'en':'🇬🇧 Inglizcha', 'ko':'🇰🇷 Koreyscha'}
GENDERS = ['Erkak', 'Ayol']
AGES = ['15-20', '21-30', '31-40', '41+']
PROVINCES = ['Toshkent','Samarqand','Buxoro','Farg‘ona','Andijon','Surxondaryo','Qoraqalpog‘iston','Namangan','Jizzax','Navoiy','Sirdaryo','Xorazm']

# --- KEYBOARDS ---
def get_lang_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(name, callback_data=f"lang_{code}")] for code,name in LANGUAGES.items()])
def get_gender_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(g, callback_data=f"gender_{g}")] for g in GENDERS])
def get_age_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(a, callback_data=f"age_{a}")] for a in AGES])
def get_province_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton(p, callback_data=f"province_{p}")] for p in PROVINCES])
def get_chat_buttons(): 
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Keyingi", callback_data='next')],
        [InlineKeyboardButton("⏹ To‘xtatish", callback_data='stop')],
        [InlineKeyboardButton("🚫 Shikoyat", callback_data='report')]
    ])

# --- VIP CHECK ---
def check_vip(user_id):
    user = USERS.get(user_id)
    if user and user.get('vip') and user.get('vip_until'):
        if datetime.now() > user['vip_until']:
            user['vip'] = False
            user['vip_until'] = None

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if user_id not in USERS:
        USERS[user_id] = {'lang': None, 'chatting_with': None, 'vip': False, 'vip_until': None, 'refs': 0, 'profile': {}}

    # Referral
    if args and args[0].startswith("ref_"):
        inviter_id = int(args[0].split("_")[1])
        if inviter_id != user_id and inviter_id in USERS:
            USERS[inviter_id]['refs'] += 1
            if USERS[inviter_id]['refs'] >= 10 and not USERS[inviter_id]['vip']:
                USERS[inviter_id]['vip'] = True
                USERS[inviter_id]['vip_until'] = datetime.now() + timedelta(days=7)
                await context.bot.send_message(inviter_id, "🏆 Siz VIP bo‘ldingiz 7 kun!")

    # Boshlang‘ich dizayn
    intro = (
        "👋 Chat360 ga xush kelibsiz!\n\n"
        "📌 Bu botda anonim ravishda suhbat qilishingiz mumkin.\n"
        "🌐 Matn va audio yuborish mumkin.\n"
        "⚡ VIP navbat orqali tezroq suhbat topishingiz mumkin.\n"
        "👥 Do‘stlaringizni taklif qilib VIP oling!\n\n"
        f"🔗 Sizning referral linkingiz:\nhttps://t.me/{context.bot.username}?start=ref_{user_id}"
    )
    await update.message.reply_text(intro)

    # Profil so‘rash startdan keyin
    await update.message.reply_text("Iltimos, ismingizni kiriting:")

# --- PROFILE HANDLER ---
async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    profile = USERS[user_id]['profile']

    if 'name' not in profile:
        profile['name'] = text
        await update.message.reply_text("Yoshingizni tanlang:", reply_markup=get_age_keyboard())
    elif 'age' not in profile:
        profile['age'] = text
        await update.message.reply_text("Jinsingizni tanlang:", reply_markup=get_gender_keyboard())
    elif 'gender' not in profile:
        profile['gender'] = text
        await update.message.reply_text("Qayerdansiz?", reply_markup=get_province_keyboard())
    elif 'province' not in profile:
        profile['province'] = text
        await update.message.reply_text("Tilni tanlang:", reply_markup=get_lang_keyboard())

# --- BUTTON HANDLER ---
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
        return
    elif data.startswith("age_"):
        USERS[user_id]['profile']['age'] = data.split("_")[1]
        await query.answer(f"Yosh oralig‘i tanlandi: {USERS[user_id]['profile']['age']}")
        return
    elif data.startswith("province_"):
        USERS[user_id]['profile']['province'] = data.split("_")[1]
        await query.answer(f"Viloyat tanlandi: {USERS[user_id]['profile']['province']}")
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

# --- MATCH HANDLER ---
async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    check_vip(user_id)
    if user_id not in QUEUE:
        if USERS[user_id]['vip']:
            QUEUE.insert(0,user_id)
        else:
            QUEUE.append(user_id)
    await update.message.reply_text("🔎 Suhbatdosh topilmoqda...")

    while len(QUEUE)>=2:
        u1 = QUEUE.pop(0)
        u2 = QUEUE.pop(0)
        USERS[u1]['chatting_with'] = u2
        USERS[u2]['chatting_with'] = u1
        for uid in [u1,u2]:
            await context.bot.send_message(chat_id=uid, text="🆕 Suhbatdosh topildi!", reply_markup=get_chat_buttons())

# --- MESSAGE HANDLER ---
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
            text = GoogleTranslator(source=user_lang,target=partner_lang).translate(text)
        except:
            pass
    await context.bot.send_message(chat_id=partner_id,text=text)

# --- AUDIO HANDLER ---
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
        with open(filename,'rb') as f:
            await context.bot.send_voice(chat_id=partner_id,voice=f)

# --- VIP STATUS ---
async def vip_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    check_vip(user_id)
    user = USERS.get(user_id,{})
    if user.get('vip'):
        remaining = user['vip_until'] - datetime.now()
        days,hours = divmod(remaining.total_seconds(),86400)
        hours, remainder = divmod(hours,3600)
        minutes,_ = divmod(remainder,60)
        status_text = f"💎 VIP foydalanuvchi\n⏳ Qolgan vaqt: {int(days)} kun {int(hours)} soat {int(minutes)} minut"
    else: status_text="❌ Oddiy foydalanuvchi"
    refs = user.get('refs',0)
    await update.message.reply_text(f"{status_text}\n👥 Taklif qilganlar: {refs}")

# --- ADMIN DATA ---
async def admin_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    text = "📊 RAMdagi ma'lumotlar:\n\n"
    for uid,user in USERS.items():
        text += f"{uid}: {user}\n"
    await update.message.reply_text(text)

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, audio_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("vip", vip_status))
    app.add_handler(CommandHandler("admin", admin_data))
    app.add_handler(CommandHandler("match", match))

    print("✅ Bot ishga tushdi...")
    app.run_polling()
