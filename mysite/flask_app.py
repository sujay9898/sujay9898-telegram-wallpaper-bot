import os
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
import smtplib
from email.message import EmailMessage

# === Configuration ===
BOT_TOKEN = "8149637331:AAHONVcBVJ6MGzBr0CjVJZX71eA_sgphGSk"
GMAIL_USER = "filmyteacare@gmail.com"
GMAIL_PASS = "sxakhsvaumpoqbcb"
CATALOG_PATH = "catalog.pdf"  # optional PDF catalog

# === Wallpaper Data ===
wallpapers = {
    "WP1": ("Beast Mode (Red)", "Beast 1.png"),
    "WP2": ("Beast Mode (Yellow)", "Beast 2.png"),
    "WP3": ("Kendrick Live (Red)", "Kendrick 1.png"),
    "WP4": ("Kendrick Live (Blue)", "Kendrick 2.png"),
    "WP5": ("Leo Minimal (Coffee)", "Leo 1.png"),
    "WP6": ("Leo Minimal (Blood)", "Leo 2.png"),
    "WP7": ("Vintage Duo", "M 1.png"),
    "WP8": ("Smoking Chills Red Text", "Star 1.png"),
    "WP9": ("Smoking Chills Yellow Text", "Star 2.png"),
    "WP10": ("Life Itself (TK Quote)", "TK.png"),
    "WP11": ("Virat Hundred", "Virat.png"),
}

# === Flask App ===
app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()
bot = application.bot

# === States ===
GET_NAME, GET_EMAIL = range(2)
user_data = {}

# === Handlers ===

def build_keyboard():
    keyboard = []
    for key, (title, _) in wallpapers.items():
        keyboard.append([InlineKeyboardButton(f"{title}", callback_data=key)])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await bot.send_message(chat_id, "📖 Here's the wallpaper catalog PDF:")
    if os.path.exists(CATALOG_PATH):
        await bot.send_document(chat_id, document=InputFile(CATALOG_PATH))
    await bot.send_message(chat_id, "🖼 Choose a wallpaper:", reply_markup=build_keyboard())

async def handle_wallpaper_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    wallpaper_id = query.data
    context.user_data["wallpaper_id"] = wallpaper_id
    await query.message.reply_text("Please enter your name:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Please enter your email:")
    return GET_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    user = context.user_data
    wallpaper_id = user.get("wallpaper_id")
    if wallpaper_id not in wallpapers:
        await update.message.reply_text("Error: wallpaper not found.")
        return ConversationHandler.END

    name = user.get("name")
    title, filename = wallpapers[wallpaper_id]

    # === Email delivery ===
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Your wallpaper: {title}"
        msg["From"] = GMAIL_USER
        msg["To"] = email
        msg.set_content(f"Hi {name},\n\nHere's your wallpaper: {title}")

        with open(f"wallpapers/{filename}", "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename=filename)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
    except Exception as e:
        await update.message.reply_text("❌ Failed to send email.")
        return ConversationHandler.END

    # === Telegram delivery ===
    try:
        with open(f"wallpapers/{filename}", "rb") as photo:
            await bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption="✅ Sent to your email!")
    except:
        await update.message.reply_text("✅ Email sent. But Telegram image failed.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

# === Register Handlers ===
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(handle_wallpaper_selection)],
    states={
        GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(conv_handler)

# === Flask Webhook Endpoint (non-async) ===
@app.route('/', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return 'ok'

# Optional health check
@app.route('/')
def index():
    return 'Telegram bot is live.'
