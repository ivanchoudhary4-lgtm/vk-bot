import os
import threading
import logging
from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Render dummy web server
server = Flask(__name__)

@server.route('/')
def home():
    return "VK International Bot is Running Superfast!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)

# Credentials
BOT_TOKEN = "8998645638:AAEem-IkFbKEj_0uXcgzaF1qipS_Y3UemJE"
ADMIN_CHAT_ID = "8638498161"

NAME, PASSPORT, JOB, EXPERIENCE, PHONE = range(5)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Step 1: Greeting & Ask Name
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    welcome_text = (
        "<b>VK International Lv</b> | European Employment Services\n"
        "────────────────────────────\n"
        "Welcome to our verified candidate registration desk for <b>Europe</b>.\n\n"
        "👉 <b> Please enter your Full Name</b> (as printed on your Passport/ID):"
    )
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    return NAME

# Step 2: Passport (Clickable Inline Buttons)
async def ask_passport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Passport Ready", callback_data="Passport: Ready")],
        [InlineKeyboardButton("⏳ Applied / In Process", callback_data="Passport: In Process")],
        [InlineKeyboardButton("❌ Don't Have Passport Yet", callback_data="Passport: None")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Thank you, <b>{context.user_data['name']}</b>.\n\n"
        "Do you currently hold an active, valid international passport?\n"
        "<i>(Click one of the options below)</i>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return PASSPORT

# Step 3: Jobs List (Clickable Inline Buttons)
async def ask_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["passport"] = query.data.replace("Passport: ", "")

    keyboard = [
        [InlineKeyboardButton("📦 Warehouse & Packaging", callback_data="Job: Warehouse & Packaging")],
        [InlineKeyboardButton("🏭 Factory & Production Worker", callback_data="Job: Factory & Production")],
        [InlineKeyboardButton("🚜 Forklift / Machine Operator", callback_data="Job: Forklift Operator")],
        [InlineKeyboardButton("🚛 Heavy Commercial Driver", callback_data="Job: Commercial Driver")],
        [InlineKeyboardButton("🏗 Construction & Skilled Trades", callback_data="Job: Construction Trades")],
        [InlineKeyboardButton("🍽 Hospitality & Food Service", callback_data="Job: Hospitality & Kitchen")],
        [InlineKeyboardButton("🔧 Other / General Work", callback_data="Job: Other Work")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        "<b>Verified Vacancies Available</b>\n\n"
        "Please select the industry matching your practical work experience:\n"
        "<i>(Click your job profile below)</i>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return JOB

# Step 4: Experience Selection (Clickable Inline Buttons)
async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["job"] = query.data.replace("Job: ", "")

    keyboard = [
        [
            InlineKeyboardButton("Fresher (0–1 yr)", callback_data="Exp: Fresher"),
            InlineKeyboardButton("1 – 2 Years", callback_data="Exp: 1-2 Years")
        ],
        [
            InlineKeyboardButton("3 – 5 Years", callback_data="Exp: 3-5 Years"),
            InlineKeyboardButton("6 – 9 Years", callback_data="Exp: 6-9 Years")
        ],
        [
            InlineKeyboardButton("10+ Years (Senior)", callback_data="Exp: 10+ Years")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"Selected Role: <b>{context.user_data['job']}</b>\n\n"
        "Select your overall verified work experience in this trade:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return EXPERIENCE

# Step 5: Mobile Number Request (With Auto-Share Button + Text Option)
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["experience"] = query.data.replace("Exp: ", "")

    contact_keyboard = [
        [KeyboardButton("📱 Tap to Share My Mobile Number", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await query.message.reply_text(
        "<b>Final Step: Verification</b>\n\n"
        "👉 Click the button below: <b>[📱 Tap to Share My Mobile Number]</b>\n\n"
        "<i>(Or simply type your 10-digit WhatsApp number with country code, e.g. +91 9876543210)</i>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return PHONE

# Final Step: Capture Lead & Alert Admin
async def finish_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
    else:
        phone = update.message.text.strip()
        
    context.user_data["phone"] = phone
    user = update.effective_user
    username_text = f"@{user.username}" if user.username else "No username"

    # User Confirmation
    success_text = (
        "✅ <b>Application Registered Successfully!</b>\n"
        "────────────────────────────\n"
        f"Candidate: <b>{context.user_data.get('name')}</b>\n"
        f"Applied Trade: <b>{context.user_data.get('job')}</b>\n"
        f"Experience: <b>{context.user_data.get('experience')}</b>\n\n"
        "Our European placement desk in Riga, Latvia has received your file.\n\n"
        "📞 A visa coordinator will review your profile and contact you on WhatsApp <b>within 24 hours</b>.\n\n"
        "<i>VK International Lv — European Placement Desk</i>"
    )
    await update.message.reply_text(success_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

    # Admin Alert
    lead_summary = (
        "🚨 <b>NEW CANDIDATE LEAD</b>\n"
        "────────────────────────────\n"
        f"👤 <b>Name:</b> {context.user_data.get('name')}\n"
        f"📱 <b>WhatsApp:</b> <code>{phone}</code>\n"
        f"🛂 <b>Passport:</b> {context.user_data.get('passport')}\n"
        f"💼 <b>Role:</b> {context.user_data.get('job')}\n"
        f"⏳ <b>Experience:</b> {context.user_data.get('experience')}\n"
        f"💬 <b>Telegram ID:</b> {username_text} (<code>{user.id}</code>)\n"
        "────────────────────────────"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=lead_summary,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Failed to forward lead to admin: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Application cancelled. Type /start to begin again.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_passport)],
            PASSPORT: [CallbackQueryHandler(ask_job)],
            JOB: [CallbackQueryHandler(ask_experience)],
            EXPERIENCE: [CallbackQueryHandler(ask_phone)],
            PHONE: [
                MessageHandler(filters.CONTACT, finish_and_save),
                MessageHandler(filters.TEXT & ~filters.COMMAND, finish_and_save),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("VK International Bot is active...")
    app.run_polling()

if __name__ == "__main__":
    main()
