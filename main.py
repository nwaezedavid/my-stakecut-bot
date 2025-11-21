import logging
import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler

# --- CONFIGURATION ---
TOKEN = "8206593551:AAHMi_AHYmJS-AcQVa0COn_0bXNCo-qQzTU"

# Your Links
CHANNEL_LINK = "https://t.me/nwaezedavid_channel"
AFFILIATE_LINK = "https://owodaily.com/champion.php?referral_code=20987346"  # Updated to OwoDaily

# WhatsApp Configuration
# We are using your specific wa.link which handles the message automatically
WHATSAPP_LINK = "https://wa.link/swsxqf"

# TIMING CONFIGURATION
# First message delay: 2 Hours = 7200 seconds
INITIAL_DELAY = 7200  
# Daily follow-up interval: 24 Hours = 86400 seconds
DAILY_INTERVAL = 86400 

# --- FOLLOW-UP SCRIPTS (30 DAYS) ---
FOLLOWUP_SCRIPTS = [
    # Day 1
    "👋 {name}, quick check-in.\nDid you successfully access the OwoDaily platform? Reply if you are having issues signing up.",
    # Day 2
    "👀 {name}, I noticed you haven't started yet.\nThe digital economy is moving fast. There is no better time to start earning than today.",
    # Day 3
    "🔥 {name}, did you see the results in the channel?\nPeople are earning daily commissions. You are next.",
    # Day 4
    "🤔 {name}, honestly asking...\nWhat is stopping you? This platform is beginner-friendly. Click the link to start.",
    # Day 5
    "🚀 Opportunity Warning.\nDon't wait until the registration requirements change. Secure your account now: {link}",
    # Day 6
    "💡 Fact: You don't need a laptop.\nThis entire business can be run from the phone you are holding right now.",
    # Day 7
    "👋 {name}, it's been a week!\nImagine if you had started 7 days ago... you'd likely be seeing results by now. Start today!",
]

# Filler for the remaining days (8-30)
GENERIC_FOLLOWUP = "💰 Just a friendly reminder: Your Daily Income potential is waiting. Tap here to start: {link}"

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- STATES ---
WELCOME, QUIZ_1, QUIZ_2, PITCH_PHASE = range(4)

# --- BOT FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Phase 1: Welcome & Channel Join (Mandatory)"""
    user_first_name = update.effective_user.first_name
    
    welcome_text = (
        f"Hi {user_first_name}! 👋\n\n"
        "I am going to show you the **No-Fail System** to earning daily income online.\n\n"
        "🚨 **STEP 1:** You must join my updates channel first so you don't miss mentorship calls.\n\n"
        f"👉 [Click Here to Join Channel]({CHANNEL_LINK})\n\n"
        "Once you have joined, click the button below."
    )
    
    keyboard = [[InlineKeyboardButton("✅ I've Joined! Continue 🚀", callback_data='joined_channel')]]
    
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return WELCOME

async def quiz_step_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Phase 2: Qualification Question 1"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "Awesome! Let's see if you qualify for this program.\n\n"
        "**Question 1:**\n"
        "To make this work, you need a smartphone and at least 1 hour a day.\n\n"
        "Do you have these?"
    )
    
    keyboard = [[InlineKeyboardButton("Yes, I have them ✅", callback_data='has_phone')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return QUIZ_1

async def quiz_step_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Phase 3: Qualification Question 2"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "Great.\n\n"
        "**Question 2:**\n"
        "This is a business for serious people who want to earn online.\n\n"
        "Are you ready to take instructions and implement what you learn?"
    )
    
    keyboard = [[InlineKeyboardButton("Yes, Show Me the Secret 💰", callback_data='ready_dollar')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return QUIZ_2

async def reveal_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Phase 4: The Pitch (Direct OwoDaily Link)"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    name = query.from_user.first_name
    
    text = (
        "🎉 **Congratulations! You are Qualified.**\n\n"
        "You have everything you need to succeed. The platform we are using is called **OwoDaily**.\n\n"
        "It allows you to earn by performing simple digital tasks or referring others.\n\n"
        "👇 **CLICK BELOW TO GET INSTANT ACCESS:**"
    )
    
    # BUTTONS UPDATED HERE
    keyboard = [
        [InlineKeyboardButton("🚀 GET ACCESS NOW", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🤔 I Have a Question", url=WHATSAPP_LINK)]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # Schedule Follow-ups
    context.job_queue.run_once(send_scheduled_message, INITIAL_DELAY, chat_id=chat_id, data={'name': name, 'day': 0})
    for day in range(1, 31):
        delay = INITIAL_DELAY + (day * DAILY_INTERVAL)
        context.job_queue.run_once(send_scheduled_message, delay, chat_id=chat_id, data={'name': name, 'day': day})
        
    return PITCH_PHASE

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    """Handles sending the delayed messages"""
    job = context.job
    data = job.data
    day_index = data['day']
    user_name = data['name']
    
    if day_index == 0:
        message_text = (
            f"👋 Hey {user_name}, just checking in.\n\n"
            "Did you manage to click the link and see the OwoDaily details?\n\n"
            "Don't let this opportunity slide. The earlier you start, the faster you earn."
        )
    else:
        script_index = day_index - 1
        if script_index < len(FOLLOWUP_SCRIPTS):
            raw_text = FOLLOWUP_SCRIPTS[script_index]
        else:
            raw_text = GENERIC_FOLLOWUP
        message_text = raw_text.format(name=user_name, link=AFFILIATE_LINK)

    # BUTTONS UPDATED HERE AS WELL
    keyboard = [
        [InlineKeyboardButton("🚀 GET ACCESS NOW", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🤔 I Have a Question", url=WHATSAPP_LINK)]
    ]
    
    await context.bot.send_message(chat_id=job.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("No problem! Please use the WhatsApp button to chat with me directly.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Okay! Type /start whenever you are ready.")
    return ConversationHandler.END

# --- WEB SERVER ---
async def health_check(request):
    return web.Response(text="Bot is Alive")

async def run_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

# --- MAIN EXECUTION ---
async def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WELCOME: [CallbackQueryHandler(quiz_step_1, pattern='^joined_channel$')],
            QUIZ_1: [CallbackQueryHandler(quiz_step_2, pattern='^has_phone$')],
            QUIZ_2: [CallbackQueryHandler(reveal_link, pattern='^ready_dollar$')],
            PITCH_PHASE: [CallbackQueryHandler(handle_questions, pattern='^ask_question$')]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv_handler)

    await run_web_server()
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    stop_signal = asyncio.Event()
    await stop_signal.wait()

if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
