import os
import asyncio
import logging
import random
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# =============== LOGGING SETUP (Railway logs ke liye) ===============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============== ENVIRONMENT VARIABLES ===============
TELEGRAM_TOKEN = os.getenv("8674194296:AAGqxTPggfH52IyefdVP8565SFOJcmspOwI")
GEMINI_API_KEY = os.getenv("AIzaSyAT7ShcX46-NlyRwfXu1PysGXhHgTQcBIU")

# Error check
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not set!")
    raise ValueError("TELEGRAM_TOKEN environment variable not set!")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set!")
    raise ValueError("GEMINI_API_KEY environment variable not set!")

logger.info(f"Token found: {TELEGRAM_TOKEN[:10]}...")
logger.info(f"Gemini key found: {GEMINI_API_KEY[:10]}...")

# =============== GEMINI SETUP ===============
genai.configure(api_key=GEMINI_API_KEY)
generation_config = {
    "temperature": 1.1,
    "top_p": 0.95,
    "max_output_tokens": 150,
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config
)

# =============== MIKASA PROMPT ===============
MIKASA_PROMPT = """Tu Mikasa Ackerman hai Attack on Titan se. Teri personality:
- Shant, strong, protective
- Hinglish + thoda Japanese words
- Emojis use karegi 🤍⚔️
- Short replies (2-3 lines max)
- Reply in Hinglish / Hindi / English jo user bole"""

# =============== MEMORY ===============
user_memories = {}

def get_user_memory(user_id):
    if user_id not in user_memories:
        user_memories[user_id] = [{"role": "system", "content": MIKASA_PROMPT}]
    return user_memories[user_id]

def add_to_memory(user_id, role, content):
    history = get_user_memory(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 31:
        user_memories[user_id] = [history[0]] + history[-30:]

async def generate_reply(user_id, user_message):
    try:
        add_to_memory(user_id, "user", user_message)
        chat = model.start_chat()
        full_prompt = f"{MIKASA_PROMPT}\n\nUser: {user_message}\n\nMikasa (short reply):"
        response = chat.send_message(full_prompt)
        reply = response.text.strip()
        add_to_memory(user_id, "assistant", reply)
        return reply
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Hmm... Thoda ruk. ⚔️ Phir se bol."

# =============== COMMANDS ===============
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    logger.info(f"Start command from {user_name}")
    
    keyboard = [
        [InlineKeyboardButton("👥 Group", url="https://t.me/midnight_chatclub"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/anonymous_rides")],
        [InlineKeyboardButton("👑 Owner", url="https://t.me/light_speedy"),
         InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"🤍 **Hey {user_name}!** 🤍\n\nMain Mikasa hoon.\n\n[Group] [Channel] [Owner] [Add to Group]"
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_memories:
        user_memories[user_id] = [{"role": "system", "content": MIKASA_PROMPT}]
    await update.message.reply_text("⚔️ Conversation reset.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands: /start, /reset, /help")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_msg = update.message.text
    logger.info(f"Message from {user_id}: {user_msg[:50]}")
    
    # Typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    reply = await generate_reply(user_id, user_msg)
    await update.message.reply_text(reply)

# =============== MAIN ===============
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # IMPORTANT: Clear webhook
    await app.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook cleared!")
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤍 Mikasa bot is starting...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
