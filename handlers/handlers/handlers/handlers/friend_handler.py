from telegram import Update
from telegram.ext import ContextTypes

async def friend_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👫 Do‘st topish xizmati:\n"
        "🔹 Random chat\n"
        "🔹 Qiz / O‘g‘il tanlash\n"
        "🔹 Yaqin hududdan odamlar"
    )
