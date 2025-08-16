from telegram import Update
from telegram.ext import ContextTypes

async def vip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "👑 VIP imkoniyatlari:\n\n"
        "✅ Cheksiz do‘st qo‘shish\n"
        "✅ Maxfiy chat\n"
        "✅ Maxsus stikerlar\n"
        "✅ VIP o‘yinlar\n\n"
        "💳 Narx: 50.000 so‘m / oy"
    )
