from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from handlers.start_handler import start
from handlers.language_handler import language_callback
from handlers.vip_handler import vip_callback
from handlers.referral_handler import referral_callback
from handlers.mini_game_handler import mini_game_callback
from handlers.friend_handler import friend_callback

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Tokeningizni shu yerga yozing

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Start komandasi
    app.add_handler(CommandHandler("start", start))

    # Callbacklar
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(vip_callback, pattern="^vip_"))
    app.add_handler(CallbackQueryHandler(referral_callback, pattern="^ref_"))
    app.add_handler(CallbackQueryHandler(mini_game_callback, pattern="^game_"))
    app.add_handler(CallbackQueryHandler(friend_callback, pattern="^friend_"))

    print("🤖 Chat360 bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
