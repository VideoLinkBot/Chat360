from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Chat360 ishlayapti!")

def main():
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
