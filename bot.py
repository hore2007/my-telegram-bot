import os
import sys
import time

# ১. লাইব্রেরির পাথ সেটআপ
user_site = os.path.expanduser('~/.local/lib/python3.10/site-packages')
if user_site not in sys.path:
    sys.path.append(user_site)

try:
    import telebot
    from telebot import types
except ModuleNotFoundError:
    os.system("pip3 install --user pytelegrambotapi requests")
    time.sleep(2)
    import telebot
    from telebot import types

# 🤖 কনফিগারেশন
BOT_TOKEN = '8901853120:AAFWduGM0qe2zD3_HYvFicvBikF8ip3LCBE'
ADMIN_ID = 7989323715  # ক্লায়েন্টের আইডি
SUPPORT_LINK = "https://t.me/AppEarnBD"
CHANNEL_LINK = "https://t.me/AppEarnBD_official"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

user_data = {}
user_states = {} 

def init_user(user_id, username):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "referrals": 0,
            "temp_method": None,
            "temp_number": None,
            "has_pending_withdraw": False
        }

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Account 👤", "Task 📝", "Wallet 💰", "Withdraw 💳", "Invite 📩", "Channel 📢", "Support Center 👥")
    return markup

def bn_to_en_numbers(number_str):
    bn_digits = "০১২৩৪৫৬৭৮৯"
    en_digits = "0123456789"
    for bn, en in zip(bn_digits, en_digits):
        number_str = number_str.replace(bn, en)
    return number_str

# --- টাস্ক স্ক্রিনশট হ্যান্ডলার ---
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'waiting_for_task_proof':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve (8 Tk)", callback_data=f"apptask:{user_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rejtask:{user_id}")
        )
        
        bot.send_photo(
            ADMIN_ID, 
            message.photo[-1].file_id, 
            caption=f"📸 New Task Proof Submission!\nUser: {message.from_user.first_name}\nID: `{user_id}`",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
        bot.send_message(message.chat.id, "✅ Screenshot submitted! Admin will verify and update your balance.")
        del user_states[user_id]

# --- টাস্ক এপ্রুভাল হ্যান্ডলার (৮ টাকা) ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("apptask:", "rejtask:")))
def admin_task_callback(call):
    try:
        action_type, target_user_id = call.data.split(":")
        target_user_id = int(target_user_id)
        
        init_user(target_user_id, "User")
        
        if action_type == "apptask":
            user_data[target_user_id]['balance'] += 8.0 # রিওয়ার্ড ৮ টাকা
            bot.answer_callback_query(call.id, "Task Approved! 8 Tk added.")
            bot.send_message(target_user_id, "🎉 Congratulations! Your task has been approved. 8 Tk added to your balance.")
            bot.edit_message_caption(caption="✅ Approved by Admin (8 Tk Added)", chat_id=call.message.chat.id, message_id=call.message.message_id)
            
        elif action_type == "rejtask":
            bot.answer_callback_query(call.id, "Task Rejected!")
            bot.send_message(target_user_id, "❌ Your task was rejected. Please try again with a valid screenshot.")
            bot.edit_message_caption(caption="❌ Rejected by Admin", chat_id=call.message.chat.id, message_id=call.message.message_id)
            
    except Exception as e:
        print(f"Task Approval Error: {e}")

# --- উইথড্র এপ্রুভাল হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("appwd:", "rejwd:")))
def admin_withdraw_callback(call):
    try:
        data_parts = call.data.split(":")
        action_type = data_parts[0]
        target_user_id = int(data_parts[1])
        amount = float(data_parts[2]) if len(data_parts) > 2 else 0.0
        
        init_user(target_user_id, "User")
        
        if action_type == "appwd":
            user_data[target_user_id]['has_pending_withdraw'] = False
            bot.answer_callback_query(call.id, "Withdrawal Approved!")
            bot.send_message(target_user_id, "🎉 Your withdrawal request has been completed! Money has been sent to your account.")
            bot.edit_message_text("✅ Withdrawal Paid & Completed", chat_id=call.message.chat.id, message_id=call.message.message_id)
            
        elif action_type == "rejwd":
            user_data[target_user_id]['balance'] += amount
            user_data[target_user_id]['has_pending_withdraw'] = False
            bot.answer_callback_query(call.id, "Withdrawal Rejected!")
            bot.send_message(target_user_id, f"❌ Your withdrawal request was rejected. {amount} Tk has been refunded to your balance.")
            bot.edit_message_text("❌ Withdrawal Request Rejected & Refunded", chat_id=call.message.chat.id, message_id=call.message.message_id)
            
    except Exception as e:
        print(f"Withdraw Approval Error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    init_user(user_id, message.from_user.first_name)
    text = message.text

    menu_buttons = ["Account 👤", "Task 📝", "Wallet 💰", "Withdraw 💳", "Invite 📩", "Channel 📢", "Support Center 👥"]
    if text in menu_buttons and user_id in user_states and user_states[user_id] in ['waiting_number', 'waiting_amount']:
        del user_states[user_id]

    # উইথড্র ধাপ ১: নম্বর গ্রহণ
    if user_id in user_states and user_states[user_id] == 'waiting_number':
        formatted_num = bn_to_en_numbers(text)
        user_data[user_id]['temp_number'] = formatted_num
        user_states[user_id] = 'waiting_amount'
        
        curr_bal = user_data[user_id]['balance']
        bot.send_message(
            message.chat.id, 
            f"✅ Number saved: `{formatted_num}`\n"
            f"💰 Current Balance: `{curr_bal} Tk`\n\n"
            f"💵 Now enter the Amount you want to withdraw:",
            parse_mode="Markdown"
        )
        return

    # উইথড্র ধাপ ২: অ্যামাউন্ট গ্রহণ (মিনিমাম ১০০ টাকা)
    elif user_id in user_states and user_states[user_id] == 'waiting_amount':
        amount_text = bn_to_en_numbers(text)
        
        try:
            amount = float(amount_text)
        except ValueError:
            bot.send_message(message.chat.id, "❌ Invalid Amount! Please enter numbers only (e.g., 100):")
            return

        current_bal = user_data[user_id]['balance']
        
        if amount < 100.0: # মিনিমাম ১০০ টাকা লিমিট
            bot.send_message(
                message.chat.id, 
                f"❌ Minimum withdraw amount is **100 Tk**.\nYour current balance: `{current_bal} Tk`\n\nPlease enter a valid amount:",
                parse_mode="Markdown"
            )
            return
            
        if amount > current_bal:
            bot.send_message(
                message.chat.id, 
                f"❌ Insufficient balance!\n\nYour current balance is `{current_bal} Tk`. You cannot withdraw `{amount} Tk`.",
                parse_mode="Markdown"
            )
            return

        user_data[user_id]['balance'] -= amount
        user_data[user_id]['has_pending_withdraw'] = True
        method = user_data[user_id]['temp_method']
        number = user_data[user_id]['temp_number']
        
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ Complete Payment", callback_data=f"appwd:{user_id}:{amount}"),
            types.InlineKeyboardButton("❌ Reject Request", callback_data=f"rejwd:{user_id}:{amount}")
        )
        
        admin_msg = (
            f"🚨 **New Withdraw Request!**\n\n"
            f"👤 User: {message.from_user.first_name}\n"
            f"🆔 ID: `{user_id}`\n"
            f"💳 Method: {method}\n"
            f"📱 Number: `{number}` (Click to Copy)\n"
            f"💵 Amount: {amount} Tk\n\n"
            f"⚡ Please pay manually and select an action below:"
        )
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown", reply_markup=admin_markup)
        
        del user_states[user_id]
        bot.send_message(
            message.chat.id, 
            f"✅ Withdrawal Request Submitted!\n"
            f"Remaining Balance: `{user_data[user_id]['balance']} Tk`\n\n"
            f"Admin will verify soon.", 
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return

    # 🔘 মেনু বাটন হ্যান্ডলিং
    if text == "Task 📝":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📤 Upload Screenshot Proof", callback_data="upload_proof"))
        bot.send_message(message.chat.id, "🎯 Available Tasks:\n1. Download App & Review.\n\nInstructions: Download the app from the provided link and submit a screenshot here.\n💰 Reward: 8 Tk", reply_markup=markup)
    
    elif text == "Wallet 💰":
        bot.send_message(message.chat.id, f"💳 Wallet Details\n\nBalance: {user_data[user_id]['balance']} Tk\nStatus: Active ✅")
        
    elif text == "Withdraw 💳":
        balance = user_data[user_id]['balance']
        if user_data[user_id]['has_pending_withdraw']:
            bot.send_message(message.chat.id, "⏳ **আপনার একটি উইথড্র রিকোয়েস্ট পেন্ডিং আছে!**\n\nএডমিন এটি প্রসেস না করা পর্যন্ত আপনি নতুন কোনো উইথড্র রিকোয়েস্ট পাঠাতে পারবেন না।", parse_mode="Markdown")
        elif balance < 100.0: # মিনিমাম ১০০ টাকা লিমিট চেক
            bot.send_message(message.chat.id, f"❌ Minimum withdraw amount is **100 Tk**.\nYour current balance: `{balance} Tk`", parse_mode="Markdown")
        else:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("💳 Bkash", callback_data="withdraw_bkash"), 
                       types.InlineKeyboardButton("💳 Nagad", callback_data="withdraw_nagad"))
            bot.send_message(message.chat.id, f"💸 Select Method:\n\n💰 Your Current Balance: `{balance} Tk`", parse_mode="Markdown", reply_markup=markup)

    elif text == "Invite 📩":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        refer_msg = f"👥 Referral Program:\n\nEarn 5 Tk per referral!\n\n🔗 Your Referral Link:\n{ref_link}"
        bot.send_message(message.chat.id, refer_msg)

    elif text == "Support Center 👥":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Contact Admin", url=SUPPORT_LINK))
        bot.send_message(message.chat.id, "👥 Support Center:", reply_markup=markup)
        
    elif text == "Account 👤":
        data = user_data[user_id]
        profile_msg = (
            "📋 Profile Info:\n\n"
            f"👤 Name: {message.from_user.first_name}\n"
            f"🆔 ID: {user_id}\n"
            f"💰 Current Balance: {data['balance']} Tk\n"
            f"👥 Total Referrals: {data['referrals']} members"
        )
        bot.send_message(message.chat.id, profile_msg)

    elif text == "Channel 📢":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Join Channel", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, "📢 Join our official channel:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_"))
def callback_withdraw_method(call):
    user_id = call.from_user.id
    if user_data[user_id]['has_pending_withdraw']:
        bot.answer_callback_query(call.id, "আপনার একটি উইথড্র রিকোয়েস্ট পেন্ডিং আছে!", show_alert=True)
        return
    method = call.data.split("_")[1].upper()
    user_data[user_id]['temp_method'] = method
    user_states[user_id] = 'waiting_number'
    
    curr_bal = user_data[user_id]['balance']
    bot.edit_message_text(f"✅ Method Selected: **{method}**\n💰 Current Balance: `{curr_bal} Tk`\n\n📱 Please send your mobile number:", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "upload_proof")
def request_proof(call):
    user_states[call.from_user.id] = 'waiting_for_task_proof'
    bot.answer_callback_query(call.id, "Please send your screenshot now.")
    bot.send_message(call.message.chat.id, "📸 Please upload your task screenshot now.")

print("🚀 Bot running with 8 Tk Task & 100 Tk Min Withdraw...")
bot.polling(none_stop=True)