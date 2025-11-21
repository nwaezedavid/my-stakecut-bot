import logging
import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler

# --- CONFIGURATION ---
# 1. Your Specific Bot Token (Updated)
TOKEN = "8206593551:AAHMi_AHYmJS-AcQVa0COn_0bXNCo-qQzTU"

# 2. Your Affiliate Links
LEAD_MAGNET_LINK = "https://youtu.be/uPNy9X31-bs"
AFFILIATE_LINK = "https://aff.stakecut.com/503/459513"

# 3. Timing (Seconds). 
# Currently set to 30 seconds for you to test it yourself.
# BEFORE you sleep or share the link, change this to 7200 (2 hours).
FOLLOWUP_DELAY = 30 

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
    
    await query.edit_message_text(
        text=f"Awesome! Here is the **Free Explanation Video**.\n\n"
             f"👇 **Click to Watch:**\n{LEAD_MAGNET_LINK}\n\n"
             f"It reveals the exact steps. Watch it now (15 mins)."
    )
    
    # Schedule the Automatic Follow-up
    context.job_queue.run_once(send_pitch_followup, FOLLOWUP_DELAY, chat_id=chat_id, data=query.from_user.first_name)
    return VIDEO_PHASE

async def send_pitch_followup(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    pitch_text = (
        f"👋 Hey {job.data}, I hope you watched the video!\n\n"
        "🚀 **Quick Update:** The registration for the **A-Z Affiliate Marketing Program** is filling up fast.\n"
        "Click below to get the **Discounted Access**:"
    )
    keyboard = [
        [InlineKeyboardButton("💰 Get Started Now", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("🤔 I Have a Question", callback_data='ask_question')]
    ]
    await context.bot.send_message(chat_id=job.chat_id, text=pitch_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("No problem! Type your question here and I (the human admin) will reply shortly.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Okay! Type /start whenever you are ready.")
    return ConversationHandler.END

# --- WEB SERVER (KEEPS BOT ALIVE) ---
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
    # Build Bot
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

    # Start Web Server & Bot Together
    await run_web_server()
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Keep running forever
    stop_signal = asyncio.Event()
    await stop_signal.wait()

if __name__ == '__main__':
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:

        pass
        
