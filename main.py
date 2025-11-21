import logging
import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler

# --- CONFIGURATION ---
TOKEN = "8206593551:AAHMi_AHYmJS-AcQVa0COn_0bXNCo-qQzTU"

# Your Links
LEAD_MAGNET_LINK = "https://youtu.be/uPNy9X31-bs"
AFFILIATE_LINK = "https://aff.stakecut.com/503/459513"

# TIMING CONFIGURATION
# First message delay (The "Pitch" after video): 2 Hours = 7200 seconds
INITIAL_DELAY = 7200  
# Daily follow-up interval: 24 Hours = 86400 seconds
DAILY_INTERVAL = 86400 

# --- FOLLOW-UP SCRIPTS (30 DAYS) ---
# The bot will cycle through these. You can edit the text inside the quotes.
FOLLOWUP_SCRIPTS = [
    # Day 1
    "👋 {name}, quick check-in.\nDid you get a chance to finish the video? The strategy works best when you start immediately.",
    # Day 2
    "👀 {name}, I noticed you haven't started yet.\nIs there something confusing you about the Affiliate model? Reply here!",
    # Day 3 (Social Proof)
    "🔥 {name}, look at this!\nAnother student just made their first $50 using the exact method in the video. You could be next.",
    # Day 4
    "🤔 {name}, honestly asking...\nWhat is stopping you? $500/month is very realistic with this program. Click the link to start.",
    # Day 5
    "🚀 Price Increase Warning.\nThe mentorship price might go up soon. Secure your spot now: {link}",
    # Day 6
    "💡 Fact: You don't need a laptop.\nThis entire business can be run from the phone you are holding right now.",
    # Day 7
    "👋 {name}, it's been a week!\nImagine if you had started 7 days ago... you'd likely have your first sale by now. Start today!",
]

# Filler for the remaining days (8-30) to keep them engaged
GENERIC_FOLLOWUP = "💰 Just a friendly reminder: The Dollar Income goal is still waiting for you. Tap here to start: {link}"

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- STATES ---
WELCOME, VIDEO_PHASE, PITCH_PHASE = range(3)

# --- BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    welcome_text = (
        f"Hi {user_first_name}! 👋\n\n"
        "I'm excited to help you start earning in Dollars with the **A-Z of Affiliate Marketing**.\n\n"
        "⚠️ **IMPORTANT:** Before I send the free training, please join our updates channel."
    )
    keyboard = [[InlineKeyboardButton("✅ I'm Ready!", callback_data='ready_for_video')]]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return WELCOME

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    name = query.from_user.first_name
    
    # 1. Send Video
    await query.edit_message_text(
        text=f"Awesome! Here is the **Free Explanation Video**.\n\n"
             f"👇 **Click to Watch:**\n{LEAD_MAGNET_LINK}\n\n"
             f"It reveals the exact steps. Watch it now (15 mins)."
    )
    
    # 2. Schedule the IMMEDIATE Pitch (2 Hours later)
    # We pass 'day': 0 to indicate this is the main pitch
    context.job_queue.run_once(
        send_scheduled_message, 
        INITIAL_DELAY, 
        chat_id=chat_id, 
        data={'name': name, 'day': 0}
    )
    
    # 3. Schedule the 30-DAY Follow-up Sequence
    # We loop from Day 1 to Day 30
    for day in range(1, 31):
        delay = INITIAL_DELAY + (day * DAILY_INTERVAL)
        context.job_queue.run_once(
            send_scheduled_message, 
            delay, 
            chat_id=chat_id, 
            data={'name': name, 'day': day}
        )
        
    return VIDEO_PHASE

async def send_scheduled_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    day_index = data['day']
    user_name = data['name']
    
    # Decide which message to send
    if day_index == 0:
        # This is the Main Pitch (2 Hours)
        message_text = (
            f"👋 Hey {user_name}, I hope you watched the video!\n\n"
            "It's mind-blowing how simple the business model is, right?\n\n"
            "🚀 **Quick Update:** The registration for the **A-Z Affiliate Marketing Program** is filling up fast.\n"
            "Click below to get the **Discounted Access**:"
        )
    else:
        # This is a Daily Follow-up (Days 1-30)
        # We check if we have a specific script for this day, otherwise use generic
        script_index = day_index - 1
        if script_index < len(FOLLOWUP_SCRIPTS):
            raw_text = FOLLOWUP_SCRIPTS[script_index]
        else:
            raw_text = GENERIC_FOLLOWUP
            
        # Format the text with user's name and link
        message_text = raw_text.format(name=user_name, link=AFFILIATE_LINK)

    # Add Buttons
    keyboard = [
        [InlineKeyboardButton("💰 Get Started Now", url=AFFILIATE_LINK)],
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
            WELCOME: [CallbackQueryHandler(send_video, pattern='^ready_for_video$')],
            VIDEO_PHASE: [],
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
        
