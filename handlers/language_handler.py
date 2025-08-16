from telegram import Update
from telegram.ext import ContextTypes

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]

    if lang == "uz":
        text = "🇺🇿 O'zbekcha tanlandi!\nVIP, o‘yinlar va do‘stlar sizni kutmoqda."
    elif lang == "ru":
        text = "🇷🇺 Русский выбран!\nVIP, игры и новые друзья ждут вас."
    elif lang == "en":
        text = "🇬🇧 English selected!\nVIP, games and new friends are waiting for you."
    elif lang == "kr":
        text = "🇰🇷 한국어 선택됨!\nVIP, 게임 및 새 친구가 기다리고 있습니다."
    else:
        text = "❌ Xato!"

    await query.edit_message_text(text=text)
