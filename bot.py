import os
import json
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ IELTS Tori Bot is Running 24/7"

# ===== YOUR BOT CODE STARTS HERE =====
# (Paste ALL your bot.py content exactly as you have it)
# ===== YOUR BOT CODE ENDS HERE =====

# Add these lines at the VERY BOTTOM of your bot.py content:
def run_bot():
    telegram_app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]},
        fallbacks=[]
    )
    telegram_app.add_handler(conv_handler)
    telegram_app.run_polling()

# Start bot in background thread
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
