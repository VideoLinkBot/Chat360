from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# Ko'p tilli xabarlar
messages = {
    "main_menu": {
        "uz": "Bu bot sizga:\n- Yangi do‘stlar topish 👥\n- Mini-o‘yinlar va testlar 🕹️\n- Maxsus VIP imkoniyatlar ⭐\n- Maxfiy xabarlar 💌\n\nBoshlash uchun quyidagi tugmani tanlang 👇",
        "ru": "Этот бот предлагает вам:\n- Найти новых друзей 👥\n- Мини-игры и тесты 🕹️\n- Специальные VIP возможности ⭐\n- Секретные сообщения 💌\n\nВыберите кнопку ниже 👇",
        "en": "This bot allows you to:\n- Find new friends 👥\n- Mini-games and quizzes 🕹️\n- Special VIP features ⭐\n- Secret messages 💌\n\nChoose a button below 👇",
        "ko": "이 봇에서는:\n- 새 친구 찾기 👥\n- 미니게임과 퀴즈 🕹️\n- 특별 VIP 기능 ⭐\n- 비밀 메시지 💌\n\n아래 버튼을 선택하세요 👇"
    }
}

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Tanlangan tilni saqlash
    lang_code = query.data.split("_")[1]
    context.bot_data["users"][user_id]["language"] = lang_code

    # Main menu tugmalari
    keyboard = [
        [InlineKeyboardButton("Do‘st topish", callback_data="friend")],
        [InlineKeyboardButton("Mini-o‘yin / test", callback_data="mini_game")],
        [InlineKeyboardButton("VIP imkoniyatlar", callback_data="vip")],
        [InlineKeyboardButton("Referral", callback_data="referral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Main menu xabarini yuborish
    await query.edit_message_text(
        messages["main_menu"][lang_code],
        reply_markup=reply_markup
    )
