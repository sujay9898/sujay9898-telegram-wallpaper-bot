import os
os.environ["GMAIL_USER"] = "filmyteacare@gmail.com"
os.environ["GMAIL_PASSWORD"] = "sxakhsvaumpoqbcb"
os.environ["BOT_TOKEN"] = "8149637331:AAG9ejLSy5PF66Ea6KRTyGR3Kb2r0QbEmEQ"
import os
import smtplib
import threading
from flask import Flask
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler, ContextTypes
)

# === Dummy web server for Render ===
def run_web_server():
    app = Flask(__name__)

    @app.route('/')
    def index():
        print("🔥 Ping received!")
        return 'Bot is alive!'

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web_server, daemon=True).start()

# === Gmail & Bot Settings ===
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_PASSWORD")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === States ===
GET_NAME, GET_EMAIL = range(2)

# === Wallpapers ===
wallpapers = {
    "WP1": {"name": "Beast Mode (Red)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478108/33_ql13nw.png", "hd_link": "https://drive.google.com/uc?id=13H3KAcNeB3Kt35ve3ZyKkhW8lXuAqbly"},
    "WP2": {"name": "Beast Mode (Yellow)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478112/34_ck9hsa.png", "hd_link": "https://drive.google.com/uc?id=16q64tJretb9q0rPDLI0tnXu1Cn6ULsCL"},
    "WP3": {"name": "Kendrick Live (Red)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478114/30_kblz1n.png", "hd_link": "https://drive.google.com/uc?id=1xbPiuyue7cWUZbCagcEz7DDVw1bX2jAN"},
    "WP4": {"name": "Kendrick Live (Blue)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478108/31_lqd1ml.png", "hd_link": "https://drive.google.com/uc?id=1jRkY012BqMHbcPXpghNP1IxaTTWj6MEo"},
    "WP5": {"name": "Leo Minimal (Coffee)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478107/6_hhdqqb.png", "hd_link": "https://drive.google.com/uc?id=1z5E1xW_3EAnoYQmeITIlk1Je9vJegAhJ"},
    "WP6": {"name": "Leo Minimal (Blood)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478106/7_vinq87.png", "hd_link": "https://drive.google.com/uc?id=1pU9OSHl2jG6alnYzpQpX48q7nnsRsNQZ"},
    "WP7": {"name": "Vintage Duo", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478108/12_y25qc1.png", "hd_link": "https://drive.google.com/uc?id=1qXHEgASlRjmUv1qLBF5ro6wQBQh1VQDC"},
    "WP8": {"name": "Smoking Chills red Text", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478111/46_fnicon.png", "hd_link": "https://drive.google.com/uc?id=1BDFYX4gr50d5hFlOv3NZrF84UArei87F"},
    "WP9": {"name": "Smoking Chills yellow Text", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478111/45_v9kxgp.png", "hd_link": "https://drive.google.com/uc?id=1CclRXC12Vn6gP3tFw1NJwlYT7t31iW6D"},
    "WP10": {"name": "Life Itself (TK Quote)", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478112/1_ev80yl.png", "hd_link": "https://drive.google.com/uc?id=1Kd8jqCAHMmNaw8TfhBWY5Lbjy-0n1isj"},
    "WP11": {"name": "Virat Hundred", "thumb": "https://res.cloudinary.com/dxv6byz2q/image/upload/v1752478105/2_v4osgw.png", "hd_link": "https://drive.google.com/uc?id=1IufODZCwxwll0zeo23TNXqXqRlGmj1pU"},
}

import asyncio  # make sure this is at the top

# === ✅ Clean Start Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to FilmyTea Wallpapers!\n\nUse /catalog to view the collection.")

# === ✅ Updated Catalog Command ===
async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("FILMYTEA-WALLPAPER.pdf", "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename="FILMYTEA-WALLPAPER.pdf",
                caption="📖 Here's your wallpaper catalog"
            )
    except Exception as e:
        await update.message.reply_text("❌ Could not send the wallpaper catalog.")
        print("PDF Error:", e)
        return

    await asyncio.sleep(5)
    await update.message.reply_text("🎨 Did you select your wallpaper?")

    await asyncio.sleep(1)
    wp_list = "\n".join([f"🖼 {wp['name']}" for wp in wallpapers.values()])
    await update.message.reply_text(f"👇 Tap a wallpaper name below to preview:\n\n{wp_list}")

    keyboard = [
        [InlineKeyboardButton(wp["name"], callback_data=f"preview_{wp_id}")]
        for wp_id, wp in wallpapers.items()
    ]
    await update.message.reply_text("⬇️ Tap to preview:", reply_markup=InlineKeyboardMarkup(keyboard))

# === Ask Name ===
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📝 Enter your name:")
    return GET_NAME

# === Get Name ===
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📧 Now enter your email:")
    return GET_EMAIL

# === Get Email and Send ===
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    name = context.user_data.get("name", "User")
    wp_id = context.user_data.get("selected_wp")
    wp = wallpapers.get(wp_id)

    try:
        send_email(name, email, wp["name"], wp["hd_link"])
        await update.message.reply_text(f"✅ HD wallpaper sent to {email} 🎉")
        return ConversationHandler.END
    except Exception as e:
        print("❌ Email Error:", e)
        await update.message.reply_text("❌ Invalid or failed to send email. Please enter a valid email again:")
        return GET_EMAIL

# === Send Email Function ===
def send_email(name, email, wp_name, download_link):
    subject = f"Your Wallpaper: {wp_name}"
    body = f"""
    Hi {name},<br><br>
    Thanks for getting <b>{wp_name}</b> from FilmyTea!<br><br>
    👉 <a href="{download_link}">Click here to download your wallpaper</a><br><br>
    Enjoy!<br>
    — Team FilmyTea
    """

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)

# === Main App ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_name, pattern="^get_now$")],
        states={
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
        },
        fallbacks=[],
        per_message=False,
        per_chat=True
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("catalog", catalog))
    app.add_handler(CommandHandler("tap", tap))
    app.add_handler(CallbackQueryHandler(handle_preview, pattern="^preview_"))
    app.add_handler(conv_handler)

    print("✅ Bot is running...")
    app.run_polling()





