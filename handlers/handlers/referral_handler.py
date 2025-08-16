from telegram import Update
from telegram.ext import ContextTypes

async def referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ref_link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"

    await query.edit_message_text(
        f"🎁 Do‘stlaringizni taklif qiling!\n\n"
        f"👥 Sizning referral link: {ref_link}\n\n"
        "Har bir do‘st uchun bonus olasiz!"
    )
