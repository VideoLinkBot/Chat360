from telegram import Update
from telegram.ext import ContextTypes

async def friend_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Tilni aniqlash
    lang = context.bot_data["users"][user_id]["language"] if context.bot_data["users"][user_id]["language"] else "uz"

    # Do‘st topish xabarlar ko'p tilli
    friend_messages = {
        "uz": "Vooo! Siz uchun yangi do‘st tavsiya qilindi! 👥\nProfilni ko‘rish va chat boshlash uchun tugmani bosing.",
        "ru": "Vooo! Вам рекомендован новый друг! 👥\nНажмите кнопку, чтобы просмотреть профиль и начать чат.",
        "en": "Vooo! A new friend is recommended for you! 👥\nClick the button to view profile and start chat.",
        "ko": "Vooo! 새로운 친구가 추천되었습니다! 👥\n프로필을 보고 채팅을 시작하려면 버튼을 누르세요."
    }

    await query.edit_message_text(friend_messages[lang])
