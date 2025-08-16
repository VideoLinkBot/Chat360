from telegram import Update
from telegram.ext import ContextTypes
import random

async def mini_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    games = ["🎲 Kubik tashlash", "❤️ Sevgi testi", "🧠 IQ testi", "😂 Random hazil"]
    game = random.choice(games)

    await query.edit_message_text(f"O‘yinni boshlaymiz: {game}")
