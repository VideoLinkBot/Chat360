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
    is_vip = USERS[user_id].get('vip', False)
    text = "✅ VIP" if is_vip else "❌ VIP"
    keyboard = [[InlineKeyboardButton(text, callback_data='vip_status')]]
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

    # Referral orqali
    if args and args[0].startswith("ref_"):
        inviter_id = int(args[0].split("_")[1])
        if inviter_id != user_id and inviter_id in USERS:
            USERS[inviter_id]['refs'] += 1
            if USERS[inviter_id]['refs'] >= 10 and not USERS[inviter_id]['vip']:
                USERS[inviter_id]['vip'] = True
                USERS[inviter_id]['vip_until'] = datetime.now() + timedelta(days=7)
                await context.bot.send_message(inviter_id, "🏆 Tabriklaymiz! Siz VIP bo‘ldingiz 7 kun davomida!")

    # Boshlang‘ich dizayn
    intro_text = (
        "👋 **Chat360** ga xush kelibsiz!\n\n"
        "📌 Bu botda siz anonim ravishda istalgan odam bilan muloqot qilishingiz mumkin.\n"
        "🌐 Matn va audio yuborish imkoniyati mavjud.\n"
        "⚡ VIP navbat orqali suhbatdoshni tezroq topishingiz mumkin.\n"
        "👥 Do‘stlaringizni taklif qilib VIP oling!\n\n"
        f"🔗 Sizning referral linkingiz:\nhttps://t.me/{context.bot.username}?start=ref_{user_id}"
    )
    await update.message.reply_text(intro_text, parse_mode="Markdown")
    await update.message.reply_text("Tilni tanlang:", reply_markup=get_lang_keyboard())

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if 'name' not in USERS[user_id]['profile']:
        USERS[user_id]['profile']['name'] = text
        await update.message.reply_text("Yoshingizni kiriting (masalan: 23):")
    elif 'age' not in USERS[user_id]['profile']:
        if not text.isdigit():
            await update.message.reply_text("Iltimos, faqat raqam kiriting:")
            return
        USERS[user_id]['profile']['age'] = int(text)
        await update.message.reply_text("Jinsingizni kiriting (Erkak yoki Ayol):")
    elif 'gender' not in USERS[user_id]['profile']:
        if text.lower() not in ['erkak', 'ayol']:
            await update.message.reply_text("Iltimos, faqat 'Erkak' yoki 'Ayol' deb yozing:")
            return
        USERS[user_id]['profile']['gender'] = text.capitalize()
        await update.message.reply_text(
            "Qayerdansiz? (masalan: Toshkent, Samarqand, Buxoro...)"
        )
    elif 'province' not in USERS[user_id]['profile']:
        if text not in PROVINCES:
            await update.message.reply_text("Iltimos, viloyatlardan birini yozing:")
            return
        USERS[user_id]['profile']['province'] = text
        # Profil to‘liq
        await update.message.reply_text("Profilingiz saqlandi ✅")
        await update.message.reply_text(
            "VIP statusingizni tekshirish:",
            reply_markup=get_vip_keyboard(user_id)
        )
        await update.message.reply_text(
            "Endi /match buyrug‘i bilan suhbatni boshlashingiz mumkin."
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data.startswith("lang_"):
        USERS[user_id]['lang'] = data.split("_")[1]
        await query.answer(f"Til tanlandi: {USERS[user_id]['lang']}")
        await query.message.reply_text(
            "Endi profil ma’lumotlaringizni kiriting."
        )
    elif data == 'vip_status':
        check_vip(user_id)
        status = "✅ VIP" if USERS[user_id].get('vip') else "❌ VIP"
        await query.answer(f"Holatingiz: {status}")
        await query.message.reply_text(f"Sizning VIP holatingiz: {status}")

    # Chat tugmalari
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
        await query.message.reply_text("✅ Rahmat! Suhbat boshqaruvchiga yuborildi.")

# --- Match funksiyasi ---
async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if USERS[user_id]['chatting_with']:
        await context.bot.send_message(user_id, "Siz allaqachon suhbatdosh bilan ulanibsiz.")
        return
    # Oddiy navbat (VIP bo‘lsa oldinga)
    check_vip(user_id)
    if USERS[user_id].get('vip'):
        for uid in QUEUE:
            if uid != user_id:
                USERS[user_id]['chatting_with'] = uid
                USERS[uid]['chatting_with'] = user_id
                QUEUE.remove(uid)
                await context.bot.send_message(user_id, "✅ Suhbat boshlandi!", reply_markup=get_chat_buttons())
                await context.bot.send_message(uid, "✅ Suhbat boshlandi!", reply_markup=get_chat_buttons())
                return
    # Oddiy navbatga qo‘shish
    if user_id not in QUEUE:
        QUEUE.append(user_id)
        await context.bot.send_message(user_id, "🔄 Siz navbatga qo‘shildingiz, biroz kuting...")

# --- MAIN ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, profile_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot ishga tushdi...")
    app.run_polling()        
