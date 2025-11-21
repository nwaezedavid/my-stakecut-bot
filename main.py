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
AFFILIATE_LINK = "https://aff.stakecut.com/503/459513"

# TIMING CONFIGURATION
# First message delay (The "Nudge" after they get the link): 2 Hours = 7200 seconds
INITIAL_DELAY = 7200  
# Daily follow-up interval: 24 Hours = 86400 seconds
DAILY_INTERVAL = 86400 

# --- FOLLOW-UP SCRIPTS (30 DAYS) ---
# Rewritten to focus on "Accessing the Guide" instead of "Watching a Video"
FOLLOWUP_SCRIPTS = [
    # Day 1
    "👋 {name}, quick check-in.\nDid you successfully access the A-Z Affiliate Guide? Reply if you are having issues opening the link.",
    # Day 2
    "👀 {name}, I noticed you haven't started yet.\nThe Dollar exchange rate is high right now. There is no better time to earn in USD than today.",
    # Day 3 (Social Proof)
    "🔥 {name}, did you see the results in the channel?\nOrdinary people are doing this with just their smartphones. You are next.",
    # Day 4
    "🤔 {name}, honestly asking...\nWhat is stopping you? This business model is beginner-friendly. Click the link to start.",
    # Day 5
    "🚀 Price Increase Warning.\nThe mentorship price might go up soon. Secure your spot now: {link}",
    # Day 6
    "💡 Fact: You don't need a laptop.\nThis entire business can be run from the phone you are holding right now.",
    # Day 7
    "👋 {name}, it's been a week!\nImagine if you had started 7 days ago... you'd likely be setting up your funnel by now. Start today!",
]

# Filler for the remaining days (8-30)
GENERIC_FOLLOWUP = "💰 Just a friendly reminder: Your Dollar Income potential is waiting. Tap here to start: {link}"

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
        "I am going to show you the **No-Fail System** to earning in Dollars.\n\n"
        "🚨 **STEP 1:** You must join my updates channel first so you don't miss mentorship calls.\n\n"
        f"👉 [Click Here to Join Channel]({CHANNEL_LINK})\n\n"
        "Once you have joined, click the button below."
    )
    
    keyboard = [[InlineKeyboardButton("✅ I've Joined! Continue 🚀", callback_data='joined_channel')]]
    
    # Using parse_mode='Markdown' so the link works
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
    """Phase 3: Qualification Question 2 (Psychological Commitment)"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "Great.\n\n"
        "**Question 2:**\n"
        "This is a business for serious people who want to earn in Dollars and withdraw in Naira.\n\n"
        "Are you ready to take instructions and implement what you learn?"
    )
    
    keyboard = [[InlineKeyboardButton("Yes, Show Me the Secret 💰", callback_data='ready_dollar')]]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return QUIZ_2

async def reveal_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Phase 4: The Pitch (Direct Affiliate Link)"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    name = query.from_user.first_name
    
    # High-Converting Copy
    text = (
        "🎉 **Congratulations! You are Qualified.**\n\n"
        "You have everything you need to succeed. The platform that pays in Dollars is called **Stakecut**.\n\n"
        "The **A-Z Affiliate Marketing Guide** will teach you exactly how to pick products and sell them to foreigners or locals to earn commissions.\n\n"
        "👇 **CLICK BELOW TO GET INSTANT ACCESS:**"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔓 GET ACCESS NOW", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🤔 I Have a Question", callback_data='ask_question')]
    ]
    
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    # --- SCHEDULE FOLLOW-UPS ---
    # 1. Immediate Nudge (2 Hours later)
    context.job_queue.run_once(
        send_scheduled_message, 
        INITIAL_DELAY, 
        chat_id=chat_id, 
        data={'name': name, 'day': 0}
    )
    
    # 2. 30-Day Sequence
    for day in range(1, 31):
        delay = INITIAL_DELAY + (day * DAILY_INTERVAL)
        context.job_queue.run_once(
            send_scheduled_message, 
            delay, 
            chat_id=chat_id, 
            data={'name': name, 'day': day}
        )
        
    return PITCH_PHASE

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    """Handles sending the delayed messages"""
    job = context.job
    data = job.data
    day_index = data['day']
    user_name = data['name']
    
    if day_index == 0:
        # 2-Hour Follow-up
        message_text = (
            f"👋 Hey {user_name}, just checking in.\n\n"
            "Did you manage to click the link and see the A-Z Program details?\n\n"
            "Don't let this opportunity slide. The earlier you start, the faster you earn."
        )
    else:
        # Daily Follow-up
        script_index = day_index - 1
        if script_index < len(FOLLOWUP_SCRIPTS):
            raw_text = FOLLOWUP_SCRIPTS[script_index]
        else:
            raw_text = GENERIC_FOLLOWUP
            
        message_text = raw_text.format(name=user_name, link=AFFILIATE_LINK)

    # Always include the link button
    keyboard = [
        [InlineKeyboardButton("🔓 GET ACCESS NOW", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🤔 I Have a Question", callback_data='ask_question')]
    ]
    
    await context.bot.send_message(chat_id=job.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("No problem! Type your question here and I (the human admin) will reply shortly.")
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
        
