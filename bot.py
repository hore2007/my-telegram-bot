import os
import sys
import time
from flask import Flask
from threading import Thread

# ----------------- WEB SERVER SET UP FOR RENDER -----------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------------------------------------

user_site = os.path.expanduser('~/.local/lib/python3.10/site-packages')
if user_site not in sys.path:
    sys.path.append(user_site)

try:
    import telebot
    from telebot import types
except ModuleNotFoundError:
    os.system("pip3 install --user pytelegrambotapi requests flask")
    time.sleep(2)
    import telebot
    from telebot import types

# 🤖 কনফিগারেশন
BOT_TOKEN = '8901853120:AAFWduGM0qe2zD3_HYvFicvBikF8ip3LCBE'
ADMIN_ID = 6784510011  # আপনার আইডি সেট করা হয়েছে
SUPPORT_LINK = "https://t.me/AppEarnBD"
CHANNEL_LINK = "https://t.me/AppEarnBD_official"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

user_data = {}
user_states = {} 
admin_temp_task = {}

# 🎯 একাধিক টাস্ক জমানোর লিস্ট
tasks_list = [
    {
        "id": 1,
        "desc": "Download App & Review",
        "link": "https://t.me/AppEarnBD",
        "reward": 8.0
    }
]

def init_user(user_id, username="User"):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "referrals": 0,
            "referred_by": None,
            "temp_method": None,
            "temp_number": None,
            "temp_task_id": None,
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

# --- স্টার্ট কমান্ড (/start) ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    is_new_user = user_id not in user_data
    
    init_user(user_id, message.from_user.first_name)

    text_args = message.text.split()
    if len(text_args) > 1 and is_new_user:
        ref_code = text_args[1]
        if ref_code.startswith("ref_"):
            try:
                referrer_id = int(ref_code.replace("ref_", ""))
                if referrer_id != user_id and referrer_id in user_data:
                    user_data[referrer_id]['balance'] += 5.0
                    user_data[referrer_id]['referrals'] += 1
                    user_data[user_id]['referred_by'] = referrer_id
                    
                    try:
                        bot.send_message(
                            referrer_id, 
                            f"🎉 **New Referral!**\n{message.from_user.first_name} joined using your link.\n💰 **5.00 Tk** added to your balance!",
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
            except ValueError:
                pass

    bot.send_message(
        message.chat.id, 
        f"👋 Welcome {message.from_user.first_name}!\nSelect an option below to start earning.", 
        reply_markup=main_menu()
    )

# --- 👑 নতুন টাস্ক যোগ করার এডমিন কমান্ড (/addtask) ---
@bot.message_handler(commands=['addtask'])
def add_task_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    user_states[ADMIN_ID] = 'admin_waiting_desc'
    admin_temp_task[ADMIN_ID] = {}
    bot.send_message(ADMIN_ID, "⚙️ **Add New Task**\n\nপ্রথমে নতুন টাস্কের নাম বা বিবরণ লিখে পাঠান:")

# --- 👑 টাস্ক ডিলিট করার এডমিন কমান্ড (/deltask) ---
@bot.message_handler(commands=['deltask'])
def del_task_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    if not tasks_list:
        bot.send_message(ADMIN_ID, "❌ বর্তমানে কোনো টাস্ক যুক্ত নেই।")
        return

    markup = types.InlineKeyboardMarkup()
    for task in tasks_list:
        markup.add(types.InlineKeyboardButton(f"❌ Delete: {task['desc']} ({task['reward']} Tk)", callback_data=f"remove_task:{task['id']}"))
        
    bot.send_message(ADMIN_ID, "🗑️ ডিলিট করতে চাওয়া টাস্কটির ওপর ক্লিক করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_task:"))
def remove_task_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    task_id = int(call.data.split(":")[1])
    global tasks_list
    tasks_list = [t for t in tasks_list if t['id'] != task_id]
    
    bot.answer_callback_query(call.id, "Task deleted successfully!")
    bot.edit_message_text("✅ টাস্কটি তালিকা থেকে ডিলিট করা হয়েছে।", chat_id=call.message.chat.id, message_id=call.message.message_id)

# --- টাস্ক স্ক্রিনশট হ্যান্ডলার ---
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'waiting_for_task_proof':
        task_id = user_data[user_id].get('temp_task_id')
        
        # নির্দিষ্ট টাস্ক থেকে রিওয়ার্ড অ্যামাউন্ট বের করা
        task = next((t for t in tasks_list if t['id'] == task_id), None)
        reward_amt = task['reward'] if task else 8.0
        task_name = task['desc'] if task else "Task"

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(f"✅ Approve ({reward_amt} Tk)", callback_data=f"apptask:{user_id}:{reward_amt}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rejtask:{user_id}")
        )
        
        bot.send_photo(
            ADMIN_ID, 
            message.photo[-1].file_id, 
            caption=f"📸 **New Task Proof Submission!**\nUser: {message.from_user.first_name}\nID: `{user_id}`\nTask: **{task_name}**\nReward: **{reward_amt} Tk**",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
        bot.send_message(message.chat.id, "✅ Screenshot submitted! Admin will verify and update your balance.")
        del user_states[user_id]

# --- টাস্ক এপ্রুভাল হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("apptask:", "rejtask:")))
def admin_task_callback(call):
    try:
        data_parts = call.data.split(":")
        action_type = data_parts[0]
        target_user_id = int(data_parts[1])
        
        init_user(target_user_id)
        
        if action_type == "apptask":
            reward_amt = float(data_parts[2]) if len(data_parts) > 2 else 8.0
            user_data[target_user_id]['balance'] += reward_amt
            bot.answer_callback_query(call.id, f"Task Approved! {reward_amt} Tk added.")
            bot.send_message(target_user_id, f"🎉 Congratulations! Your task has been approved. {reward_amt} Tk added to your balance.")
            bot.edit_message_caption(caption=f"✅ Approved by Admin ({reward_amt} Tk Added)", chat_id=call.message.chat.id, message_id=call.message.message_id)
            
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
        
        init_user(target_user_id)
        
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

    # 👑 নতুন টাস্ক যোগ করার এডমিন ডায়ালগ
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states[user_id]
        if state == 'admin_waiting_desc':
            admin_temp_task[ADMIN_ID]['desc'] = text
            user_states[user_id] = 'admin_waiting_link'
            bot.send_message(ADMIN_ID, "🔗 এবার অ্যাপের ডাউনলোডের **লিংক (Link)** লিখে পাঠান:")
            return
            
        elif state == 'admin_waiting_link':
            admin_temp_task[ADMIN_ID]['link'] = text
            user_states[user_id] = 'admin_waiting_reward'
            bot.send_message(ADMIN_ID, "💰 এবার এই টাস্কের **রিওয়ার্ড/টাকা** লিখুন (যেমন: 10 বা 15):")
            return
            
        elif state == 'admin_waiting_reward':
            try:
                reward = float(bn_to_en_numbers(text))
                new_id = int(time.time())
                tasks_list.append({
                    "id": new_id,
                    "desc": admin_temp_task[ADMIN_ID]['desc'],
                    "link": admin_temp_task[ADMIN_ID]['link'],
                    "reward": reward
                })
                del user_states[user_id]
                del admin_temp_task[ADMIN_ID]
                bot.send_message(
                    ADMIN_ID, 
                    f"🎉 **New Task Added Successfully!**\n\n"
                    f"মেইন মেনুর Task বাটনে এই নতুন টাস্কটি যুক্ত হয়ে গেছে।"
                )
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ ভুল সংখ্যা! অনুগ্রহ করে সংখ্যায় লিখুন (যেমন: 10):")
            return

    menu_buttons = ["Account 👤", "Task 📝", "Wallet 💰", "Withdraw 💳", "Invite 📩", "Channel 📢", "Support Center 👥"]
    if text in menu_buttons and user_id in user_states and user_states[user_id] in ['waiting_number', 'waiting_amount']:
        del user_states[user_id]

    # উইথড্র ধাপ ১
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

    # উইথড্র ধাপ ২
    elif user_id in user_states and user_states[user_id] == 'waiting_amount':
        amount_text = bn_to_en_numbers(text)
        
        try:
            amount = float(amount_text)
        except ValueError:
            bot.send_message(message.chat.id, "❌ Invalid Amount! Please enter numbers only (e.g., 100):")
            return

        current_bal = user_data[user_id]['balance']
        
        if amount < 100.0:
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
        if not tasks_list:
            bot.send_message(message.chat.id, "❌ No tasks available right now. Please check back later!")
            return

        markup = types.InlineKeyboardMarkup()
        for task in tasks_list:
            markup.add(types.InlineKeyboardButton(f"📌 {task['desc']} ({task['reward']} Tk)", callback_data=f"view_task:{task['id']}"))
            
        bot.send_message(message.chat.id, "🎯 **Available Tasks:**\nনিচের তালিকা থেকে একটি টাস্ক নির্বাচন করুন:", parse_mode="Markdown", reply_markup=markup)
    
    elif text == "Wallet 💰":
        bot.send_message(message.chat.id, f"💳 Wallet Details\n\nBalance: {user_data[user_id]['balance']} Tk\nStatus: Active ✅", reply_markup=main_menu())
        
    elif text == "Withdraw 💳":
        balance = user_data[user_id]['balance']
        if user_data[user_id]['has_pending_withdraw']:
            bot.send_message(message.chat.id, "⏳ **আপনার একটি উইথড্র রিকোয়েস্ট পেন্ডিং আছে!**\n\nএডমিন এটি প্রসেস না করা পর্যন্ত আপনি নতুন কোনো উইথড্র রিকোয়েস্ট পাঠাতে পারবেন না।", parse_mode="Markdown", reply_markup=main_menu())
        elif balance < 100.0:
            bot.send_message(message.chat.id, f"❌ Minimum withdraw amount is **100 Tk**.\nYour current balance: `{balance} Tk`", parse_mode="Markdown", reply_markup=main_menu())
        else:
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(types.InlineKeyboardButton("💳 Bkash", callback_data="withdraw_bkash"), 
                       types.InlineKeyboardButton("💳 Nagad", callback_data="withdraw_nagad"))
            bot.send_message(message.chat.id, f"💸 Select Method:\n\n💰 Your Current Balance: `{balance} Tk`", parse_mode="Markdown", reply_markup=markup)

    elif text == "Invite 📩":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        refer_msg = f"👥 Referral Program:\n\nEarn 5 Tk per referral!\n\n🔗 Your Referral Link:\n{ref_link}"
        bot.send_message(message.chat.id, refer_msg, reply_markup=main_menu())

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
        bot.send_message(message.chat.id, profile_msg, reply_markup=main_menu())

    elif text == "Channel 📢":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Join Channel", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, "📢 Join our official channel:", reply_markup=markup)

# --- ইউজার নির্দিষ্ট টাস্ক দেখার হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("view_task:"))
def view_task_callback(call):
    task_id = int(call.data.split(":")[1])
    task = next((t for t in tasks_list if t['id'] == task_id), None)
    
    if not task:
        bot.answer_callback_query(call.id, "Task not found or deleted!", show_alert=True)
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📥 Download App", url=task['link']),
        types.InlineKeyboardButton("📤 Upload Screenshot Proof", callback_data=f"upload_proof:{task['id']}")
    )
    
    task_msg = (
        f"🎯 **Task Details:**\n"
        f"📌 {task['desc']}\n\n"
        f"📖 **Instructions:** Download the app from the link below, complete the task, and upload the proof screenshot.\n"
        f"💰 **Reward:** {task['reward']} Tk"
    )
    bot.send_message(call.message.chat.id, task_msg, parse_mode="Markdown", reply_markup=markup)

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

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_proof"))
def request_proof(call):
    user_id = call.from_user.id
    data_parts = call.data.split(":")
    task_id = int(data_parts[1]) if len(data_parts) > 1 else None
    
    user_data[user_id]['temp_task_id'] = task_id
    user_states[user_id] = 'waiting_for_task_proof'
    bot.answer_callback_query(call.id, "Please send your screenshot now.")
    bot.send_message(call.message.chat.id, "📸 Please upload your task screenshot now.")

if __name__ == '__main__':
    keep_alive()
    print("🚀 Bot running with Unlimited Multi-Tasks & Admin Management...")
    bot.polling(none_stop=True)