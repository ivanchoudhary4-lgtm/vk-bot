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
    return "VK International Bot is Running Live!"

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
        "Welcome to our official candidate registration portal.\n\n"
        "We arrange verified employment contracts and official residency work permits for <b>Latvia, Poland, and Germany</b>.\n\n"
        "👉 Please enter your <b>Full Name</b> as printed on your Passport:"
    )
    await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
    return NAME

# Step 2: Passport (Clickable Inline Buttons)
async def ask_passport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    
    keyboard = [
        [
            InlineKeyboardButton("Yes, Passport Ready", callback_data="Passport: Ready"),
            InlineKeyboardButton("In Process / Applied", callback_data="Passport: In Process")
        ],
        [
            InlineKeyboardButton("No, Need Assistance", callback_data="Passport: None")
        ]
    ]
    await update.message.reply_text(
        f"Thank you, <b>{context.user_data['name']}</b>.\n\n"
        "Do you currently hold an active, valid international passport?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return PASSPORT

# Step 3: Jobs List
async def ask_job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["passport"] = query.data.replace("Passport: ", "")

    keyboard = [
        [InlineKeyboardButton("📦 Warehouse & Logistics", callback_data="Job: Warehouse & Logistics")],
        [InlineKeyboardButton("🏭 Factory & Production Worker", callback_data="Job: Factory & Production")],
        [InlineKeyboardButton("🚜 Forklift / Machine Operator", callback_data="Job: Forklift Operator")],
        [InlineKeyboardButton("🚛 Heavy Truck / Delivery Driver", callback_data="Job: Commercial Driver")],
        [InlineKeyboardButton("🏗 Construction & Skilled Trades", callback_data="Job: Construction Trades")],
        [InlineKeyboardButton("🍽 Hospitality & Food Service", callback_data="Job: Hospitality & Kitchen")]
    ]
    await query.edit_message_text(
        "<b>Verified Vacancies Available</b>\n\n"
        "Please select the industry sector that matches your practical work experience:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return JOB

# Step 4: Experience
async def ask_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["job"] = query.data.replace("Job: ", "")

    keyboard = [
        [
            InlineKeyboardButton("Fresher / Entry Level", callback_data="Exp: Fresher (0-1 yr)"),
            InlineKeyboardButton("1 – 2 Years", callback_data="Exp: 1-2 Years")
        ],
        [
            InlineKeyboardButton("3 – 5 Years", callback_data="Exp: 3-5 Years"),
            InlineKeyboardButton("6 – 9 Years", callback_data="Exp: 6-9 Years")
        ],
        [
            InlineKeyboardButton("10+ Years (Senior / Expert)", callback_data="Exp: 10+ Years")
        ]
    ]
    await query.edit_message_text(
        f"Selected Role: <b>{context.user_data['job']}</b>\n\n"
        "Select your overall verified work experience in this field:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return EXPERIENCE

# Step 5: Auto Contact Request Button
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["experience"] = query.data.replace("Exp: ", "")

    # Bada automatic contact button keyboard me dikhega
    contact_keyboard = [
        [KeyboardButton("📱 Tap to Share My WhatsApp / Mobile Number", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(contact_keyboard, resize_keyboard=True, one_time_keyboard=True)

    await query.message.reply_text(
        "<b>Final Step: Verification</b>\n\n"
        "Please click the button below to automatically share your verified mobile number for WhatsApp contact:",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    return PHONE

# Final Step: Capture Contact or Typed Number & Notify Admin
async def finish_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Auto contact share check
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
    else:
        phone = update.message.text.strip()
        
    context.user_data["phone"] = phone
    user = update.effective_user
    username_text = f"@{user.username}" if user.username else "No username"

    # User ko clean confirmation
    success_text = (
        "✅ <b>Application Registered Successfully!</b>\n"
        "────────────────────────────\n"
        f"Candidate: <b>{context.user_data.get('name')}</b>\n"
        f"Applied For: <b>{context.user_data.get('job')}</b>\n\n"
        "Our European recruitment team in Riga, Latvia has received your details.\n\n"
        "📞 A visa coordinator will review your profile and contact you on WhatsApp <b>within 24 hours</b>.\n\n"
        "<i>VK International Lv — European Placement Desk</i>"
    )
    await update.message.reply_text(success_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

    # Admin ko instant alert
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
        logging.error(f"Failed to forward lead: {e}")

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
