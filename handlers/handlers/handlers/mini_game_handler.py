from telegram import Update
from telegram.ext import ContextTypes

async def mini_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Tilni aniqlash
    lang = context.bot_data["users"][user_id]["language"] if context.bot_data["users"][user_id]["language"] else "uz"

    # Mini-o‘yinlar ro‘yxati ko'p tilli
    mini_games = {
        "uz": "🕹️ Mini-o‘yinlar:\n1. Bugun kim sizni yoqtirdi? 👀\n2. Topishmoq / Quiz\n3. Emoji challenge / Reaction game 😎\n4. Daily surprise 💌\n5. VIP-exclusive game ⭐",
        "ru": "🕹️ Мини-игры:\n1. Кто сегодня вас понравился? 👀\n2. Загадка / Quiz\n3. Emoji challenge / Reaction game 😎\n4. Daily surprise 💌\n5. VIP-exclusive game ⭐",
        "en": "🕹️ Mini-games:\n1. Who liked you today? 👀\n2. Riddle / Quiz\n3. Emoji challenge / Reaction game 😎\n4. Daily surprise 💌\n5. VIP-exclusive game ⭐",
        "ko": "🕹️ 미니게임:\n1. 오늘 누가 당신을 좋아했는지 👀\n2. 수수께끼 / Quiz\n3. Emoji challenge / Reaction game 😎\n4. Daily surprise 💌\n5. VIP-exclusive game ⭐"
    }

    await query.edit_message_text(mini_games[lang])
