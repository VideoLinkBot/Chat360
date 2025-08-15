from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.start_handler import start
from handlers.language_handler import language_callback
from handlers.vip_handler import vip_callback
from handlers.referral_handler import referral_callback
from handlers.mini_game_handler import mini_game_callback
from handlers.friend_handler import friend_callback

# Telegram bot token
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

def main():
    # Botni yaratish
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers qo'shish
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(vip_callback, pattern="^vip$"))
    app.add_handler(CallbackQueryHandler(referral_callback, pattern="^referral$"))
    app.add_handler(CallbackQueryHandler(mini_game_callback, pattern="^mini_game$"))
    app.add_handler(CallbackQueryHandler(friend_callback, pattern="^friend$"))
    app.add_handler(CallbackQueryHandler(lambda update, context: update.callback_query.answer(), pattern="^info$"))

    # Botni ishga tushurish
    print("Chat360 bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
