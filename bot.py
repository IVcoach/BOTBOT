import os
import json
import threading

# ===== IMPORTANT: COMPATIBILITY PATCH =====
import markupsafe
if not hasattr(markupsafe, 'soft_unicode'):
    markupsafe.soft_unicode = markupsafe.soft_str
# ===== END PATCH =====

from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from messages import messages
from scoring import evaluate_score

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ IELTS Bot is Running 24/7"

# Load questions
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

user_data = {}
ASKING = 1

# ===== BOT HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data[update.effective_chat.id] = {
        "current": 0,
        "score": 0,
        "lang": "en"
    }
    
    if "fa" in update.effective_user.language_code:
        user_data[update.effective_chat.id]["lang"] = "fa"
        await update.message.reply_text(messages["start_fa"])
    else:
        await update.message.reply_text(messages["start_en"])

    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data[update.effective_chat.id]
    q = questions[data["current"]]
    options = [[opt] for opt in q["options"]]
    
    prefix = f"سوال {data['current'] + 1}:" if data["lang"] == "fa" else f"Q{data['current'] + 1}:"
    await update.message.reply_text(
        f"{prefix} {q['question']}",
        reply_markup=ReplyKeyboardMarkup(options, one_time_keyboard=True)
    )
    return ASKING

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data = user_data[chat_id]
    q = questions[data["current"]]

    if update.message.text.strip() == q["answer"]:
        data["score"] += 1

    data["current"] += 1

    if data["current"] < len(questions):
        return await ask_question(update, context)
    else:
        level, ielts = evaluate_score(data["score"])
        lang = data["lang"]
        msg = messages[f"result_{lang}"].format(level=level, ielts=ielts)
        await update.message.reply_text(msg)
        return ConversationHandler.END

# ===== APPLICATION SETUP =====
def run_telegram_bot():
    application = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    # Start Telegram bot in background
    bot_thread = threading.Thread(target=run_telegram_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)
