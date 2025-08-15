from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Foydalanuvchi ma'lumotlarini saqlash (agar hali saqlanmagan bo'lsa)
    if "users" not in context.bot_data:
        context.bot_data["users"] = {}
    if user_id not in context.bot_data["users"]:
        context.bot_data["users"][user_id] = {"language": None, "vip": False, "referral": None}

    # Til tanlash tugmalari
    keyboard = [
        [
            InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
        ],
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇰🇷 한국어", callback_data="lang_ko")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Intro xabar
    intro_text = f"Vooo! 😎 {user_name}!\nChat360 dunyosiga xush kelibsiz!\nSizni yangi do‘stlar dunyosi kutmoqda! 🎉"
    
    await update.message.reply_text(intro_text, reply_markup=reply_markup)
