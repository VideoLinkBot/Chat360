from telegram import Update
from telegram.ext import ContextTypes

async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Tilni aniqlash
    lang = context.bot_data["users"][user_id]["language"] if context.bot_data["users"][user_id]["language"] else "uz"

    # Referral xabarlar ko'p tilli
    referral_messages = {
        "uz": f"💡 Do‘stlaringizni taklif qiling va bonuslar oling!\nSizning referral kodingiz: REF{user_id}",
        "ru": f"💡 Приглашайте друзей и получайте бонусы!\nВаш реферальный код: REF{user_id}",
        "en": f"💡 Invite your friends and get bonuses!\nYour referral code: REF{user_id}",
        "ko": f"💡 친구를 초대하고 보너스를 받으세요!\n당신의 추천 코드: REF{user_id}"
    }

    await query.edit_message_text(referral_messages[lang])
