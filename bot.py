import os
import threading
import logging
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Dummy web server to keep Render Free Web Service alive
server = Flask(__name__)

@server.route('/')
def home():
    return "VK International Bot is Running Live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)

# Credentials
BOT_TOKEN = "8998645638:AAEem-IkFbKEj_0uXcgzaF1qipS_Y3UemJE"
ADMIN_CHAT_ID = "8638498161"

AVAILABLE_JOBS = [
    ["Warehouse Packaging", "Factory Helper"],
    ["Forklift Operator", "Long-Haul Truck Driver"],
    ["Construction Worker", "Hotel & Kitchen Staff"],
    ["Agriculture / Farm Worker", "Welder / Fitter"],
    ["Other / General Work"]
]

NAME, PASSPORT, JOB, EXPERIENCE, PHONE = range(5)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 **Welcome to VK International Lv!**\n\n"
        "We specialize in verified employment contracts and legal European work permits (Latvia, Poland, Germany).\n\n"
        "To check your eligibility and fast-track your application, please answer a few quick questions.\n\n"
        "👉 **What is your Full Name (as per your Passport or official ID)?**",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return NAME

async def ask_passport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    reply_keyboard = [["✅ Yes, I have a valid Passport", "❌ No, I do not have one yet"]]
    await update.message.reply_text(
        f"Thank you, {context.user_data['name']}!\n\n"
        "👉 **Do you currently hold a valid international passport?**",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PASSPORT

async def ask_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["passport"] = update.message.text.strip()
    await update.message.reply_text(
        "Excellent. We currently have active hiring batches across multiple industries.\n\n"
        "👉 **Please select the role matching your primary work experience:**",
        reply_markup=ReplyKeyboardMarkup(AVAILABLE_JOBS, one_time_keyboard=True, resize_keyboard=True)
    )
    return JOB

async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["job"] = update.message.text.strip()
    exp_keyboard = [
        ["Fresher (0 Years)", "1 Year", "2 Years"],
        ["3 Years", "4 Years", "5 Years"],
        ["6-8 Years", "9-10 Years", "10+ Years"]
    ]
    await update.message.reply_text(
        f"Selected Role: *{context.user_data['job']}*\n\n"
        "👉 **How many years of relevant experience do you have in this field?**",
        reply_markup=ReplyKeyboardMarkup(exp_keyboard, one_time_keyboard=True, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return EXPERIENCE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["experience"] = update.message.text.strip()
    contact_keyboard = [
        [KeyboardButton("📱 Share Verified Mobile Number", request_contact=True)]
    ]
    await update.message.reply_text(
        "You are almost done!\n\n"
        "👉 **Please share your WhatsApp mobile number** so our European visa team can reach out to you:\n\n"
        "*(Click the button below or type your 10-digit number with country code)*",
        reply_markup=ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PHONE

async def finish_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text.strip()
        
    context.user_data["phone"] = phone
    user = update.effective_user
    username_text = f"@{user.username}" if user.username else "N/A"

    await update.message.reply_text(
        "🎉 **Application Submitted Successfully!**\n\n"
        "Your profile has been registered in our recruitment system.\n\n"
        "📞 **Next Step:** Our dedicated visa coordinator will review your file and contact you via WhatsApp or direct call **within 24 hours**.\n\n"
        "📍 **VK International Lv**\n"
        "European Recruitment & Placement Agency | Riga, Latvia",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )

    lead_summary = (
        "🚨 **NEW CANDIDATE REGISTRATION**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Candidate Name:** {context.user_data.get('name')}\n"
        f"📱 **WhatsApp / Phone:** `{phone}`\n"
        f"🛂 **Passport Status:** {context.user_data.get('passport')}\n"
        f"💼 **Applied Trade:** {context.user_data.get('job')}\n"
        f"⏳ **Experience Level:** {context.user_data.get('experience')}\n"
        f"💬 **Telegram Handle:** {username_text} (ID: `{user.id}`)\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=lead_summary,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Failed to forward lead to admin: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Application session cancelled. Type /start anytime to begin again.")
    return ConversationHandler.END

def main():
    # Start web server thread
    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_passport)],
            PASSPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_job)],
            JOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_experience)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            PHONE: [
                MessageHandler(filters.CONTACT, finish_and_save),
                MessageHandler(filters.TEXT & ~filters.COMMAND, finish_and_save),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    print("VK International Bot is active and listening...")
    app.run_polling()

if __name__ == "__main__":
    main()
