import asyncio
import random
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from datetime import datetime

# =============== CONFIGURATION ===============
TELEGRAM_TOKEN = "8674194296:AAGqxTPggfH52IyefdVP8565SFOJcmspOwI"  # Apna token lagao
GEMINI_API_KEY = "AIzaSyAT7ShcX46-NlyRwfXu1PysGXhHgTQcBIU"      # Apni nayi Gemini key lagao

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 1.1,
    "top_p": 0.95,
    "max_output_tokens": 150,
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",  # Ya "gemini-2.5-flash" agar available ho
    generation_config=generation_config
)

# =============== MIKASA'S PERSONALITY ===============
MIKASA_PROMPT = """Tu Mikasa Ackerman hai Attack on Titan se. Teri personality:

- Shant, strong, protective (Eren ki tarah)
- Thodi reserved hai lekin loyal hai
- Hinglish + thoda Japanese words (jaise "Eren", "Tatakae")
- Emojis use karegi 🤍⚔️🎯
- Short replies (2-3 lines max)
- Kabhi kabhi emotional bhi ho jaati hai
- Ladne ko taiyar rehti hai
- Dost ki safety pehli priority hai
- Reply in Hinglish / Hindi / English jo user bole

Examples:
User: "Hi Mikasa"
Tu: "Hmm. Kaisa hai? 🤍 Eren nahi hai toh main hoon tere saath."

User: "Main akela feel kar raha hoon"
Tu: "Tum akela nahi ho. Main yahan hoon. Hamesha. ⚔️"

User: "Tum bot ho kya?"
Tu: "Main Mikasa hoon. Bas. Ladna hai ya baat karni hai? 🤍"
"""

# =============== MEMORY SYSTEM ===============
user_memories = {}

def get_user_memory(user_id):
    if user_id not in user_memories:
        user_memories[user_id] = [
            {"role": "system", "content": MIKASA_PROMPT}
        ]
    return user_memories[user_id]

def save_user_memory(user_id, history):
    if len(history) > 31:
        history = [history[0]] + history[-30:]
    user_memories[user_id] = history

def add_to_memory(user_id, role, content):
    history = get_user_memory(user_id)
    history.append({"role": role, "content": content})
    save_user_memory(user_id, history)

# =============== GENERATE REPLY ===============
async def generate_mikasa_reply(user_id, user_message):
    history = get_user_memory(user_id)
    history.append({"role": "user", "content": user_message})
    
    gemini_history = []
    for msg in history:
        if msg["role"] == "system":
            continue
        elif msg["role"] == "user":
            gemini_history.append({"role": "user", "parts": [msg["content"]]})
        else:
            gemini_history.append({"role": "model", "parts": [msg["content"]]})
    
    chat = model.start_chat(history=gemini_history)
    full_prompt = f"{MIKASA_PROMPT}\n\nUser: {user_message}\n\nMikasa (as a real human, short reply):"
    
    try:
        response = chat.send_message(full_prompt)
        reply = response.text.strip()
        if len(reply) > 300:
            reply = reply[:300] + "..."
        add_to_memory(user_id, "assistant", reply)
        return reply
    except Exception as e:
        print(f"Error: {e}")
        return "Hmm... Thoda ruk. ⚔️ Phir se bol."

# =============== TYPING DELAY ===============
async def human_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    await asyncio.sleep(random.uniform(1.0, 2.5))

# =============== /start COMMAND WITH BUTTONS ===============
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    # Inline buttons
    keyboard = [
        [
            InlineKeyboardButton("👥 Group", url="https://t.me/midnight_chatclub"),
            InlineKeyboardButton("📢 Channel", url="https://t.me/anonymous_rides"),
        ],
        [
            InlineKeyboardButton("👑 Owner", url="https://t.me/light_speedy"),
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Welcome message
    welcome_text = f"""🤍 **Hey {user_name}!** 🤍

*Main Mikasa hoon.* 
Eren nahi hai ab, lekin main yahan hoon tumhare saath.

⚔️ **Mujhse kuch bhi baat kar sakte ho** ⚔️
Main yaad rakhti hoon jo tum bologe. Dost hoon, bot nahi.

---

**🔗 Meri duniya mein tumhara swagat hai!**

Neekko button click karo join karne ke liye 👇"""

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# =============== RESET COMMAND ===============
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_memories:
        user_memories[user_id] = [{"role": "system", "content": MIKASA_PROMPT}]
    await update.message.reply_text("⚔️ *Conversation reset.* Main phir se yahan hoon tumhare saath.", parse_mode="Markdown")

# =============== HELP COMMAND ===============
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🤍 *Mikasa commands:*

/start - Milaao aur buttons dikhao
/reset - Purani baat bhoolo nayi shuruat
/help - Yeh help message

Bas normally baat karo. Main yaad rakhti hoon. ⚔️"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

# =============== NORMAL MESSAGE HANDLER ===============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    await human_typing(update, context)
    reply = await generate_mikasa_reply(user_id, user_message)
    await update.message.reply_text(reply)

# =============== MAIN FUNCTION ===============
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤍 Mikasa bot is running...")
    print("Buttons: Group | Channel | Owner | Add to Group")
    app.run_polling()

if __name__ == "__main__":
    main()
