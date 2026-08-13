import telebot
from telebot import types
import os
from flask import Flask
from threading import Thread

# ---------------- WEB SERVER SET UP FOR RENDER ----------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()
# --------------------------------------------------------------

# Telegram Bot Token
TOKEN = '8901853120:AAFWduGM0qe2zD3_HYvFicvBikF8ip3LCBE'
bot = telebot.TeleBot(TOKEN)

# User database (Temporary memory)
user_data = {}

# Admin Telegram ID
ADMIN_ID = 7989323715

# Start Command
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {'balance': 0.0}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Task 📝")
    item2 = types.KeyboardButton("Balance 💰")
    item3 = types.KeyboardButton("Withdraw 💳")
    markup.add(item1, item2, item3)
    
    bot.send_message(message.chat.id, f"👋 Welcome {message.from_user.first_name}!\nSelect an option below to start earning.", reply_markup=markup)

# Handle Buttons
@bot.message_handler(content_types=['text'])
def handle_messages(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {'balance': 0.0}

    if message.text == "Task 📝":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 Upload Screenshot Proof", callback_data="upload_proof"))
        bot.send_message(
            message.chat.id, 
            "🎯 Available Tasks:\n1. Download App & Review.\n\nInstructions: Download the app from the provided link and submit a screenshot here.\n💰 Reward: 8 Tk", 
            reply_markup=markup
        )

    elif message.text == "Balance 💰":
        balance = user_data[user_id]['balance']
        bot.send_message(message.chat.id, f"💳 Your Current Balance: {balance:.2f} Tk")

    elif message.text == "Withdraw 💳":
        balance = user_data[user_id]['balance']
        if balance >= 50.0:
            bot.send_message(message.chat.id, "✅ Enter your Bkash/Nagad number to withdraw:")
        else:
            bot.send_message(message.chat.id, f"❌ Minimum withdrawal is 50 Tk.\nYour current balance is {balance:.2f} Tk.")

# Handle Proof Upload Button Click
@bot.callback_query_handler(func=lambda call: call.data == "upload_proof")
def callback_proof(call):
    msg = bot.send_message(call.message.chat.id, "Please send your screenshot proof now:")
    bot.register_next_step_handler(msg, process_screenshot)

def process_screenshot(message):
    if message.content_type == 'photo':
        photo_id = message.photo[-1].file_id
        user_id = message.chat.id
        
        # Send to Admin for Approval
        markup = types.InlineKeyboardMarkup()
        approve_btn = types.InlineKeyboardButton("✅ Approve (8 Tk)", callback_data=f"app_{user_id}")
        reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")
        markup.add(approve_btn, reject_btn)
        
        bot.send_photo(
            ADMIN_ID, 
            photo_id, 
            caption=f"📩 **New Proof Submitted!**\nUser ID: `{user_id}`\nUsername: @{message.from_user.username}", 
            parse_mode="Markdown",
            reply_markup=markup
        )
        bot.send_message(user_id, "✅ Your proof has been submitted to the admin for review!")
    else:
        bot.send_message(message.chat.id, "❌ Please send an image/screenshot only!")

# Admin Approval Callback
@bot.callback_query_handler(func=lambda call: call.data.startswith(("app_", "rej_")))
def admin_task_callback(call):
    action, target_user_id = call.data.split("_")
    target_user_id = int(target_user_id)
    
    if target_user_id not in user_data:
        user_data[target_user_id] = {'balance': 0.0}

    if action == "app":
        user_data[target_user_id]['balance'] += 8.0
        bot.send_message(target_user_id, "🎉 Congratulations! Your task proof has been approved. 8 Tk added to your balance.")
        bot.edit_message_caption("✅ Task Approved!", call.message.chat.id, call.message.message_id)
    elif action == "rej":
        bot.send_message(target_user_id, "❌ Your task proof was rejected by the admin. Please try again with valid proof.")
        bot.edit_message_caption("❌ Task Rejected!", call.message.chat.id, call.message.message_id)

# Start Web Server & Telegram Bot Polling
if __name__ == '__main__':
    keep_alive()
    bot.polling(non_stop=True)