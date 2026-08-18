import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types

# ----------------- WEB SERVER (KEEP ALIVE) -----------------
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is alive!"

def run(): 
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run).start()

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = '8901853120:AAFWduGM0qe2zD3_HYvFicvBikF8ip3LCBE'
ADMIN_ID = 6784510011

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# Data Storage
user_data = {}
user_states = {}
tasks_list = [
    {"id": 1, "desc": "Join Telegram Channel", "link": "https://t.me/AppEarnBD", "reward": 5.0}
]
withdraw_requests = []
task_proofs = []

def init_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0, 
            "referrals": 0, 
            "completed_tasks": [],
            "temp_task_id": None
        }

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Account 👤", "Task 📝", "Wallet 💰", "Withdraw 💳", "Invite 📩")
    return markup

# ----------------- USER COMMANDS -----------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    init_user(message.from_user.id)
    bot.send_message(message.chat.id, f"👋 Welcome {message.from_user.first_name}!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "Account 👤")
def account_info(message):
    u = user_data.get(message.from_user.id, {"balance": 0.0, "referrals": 0})
    bot.send_message(message.chat.id, f"👤 **Account Info**\n\n💰 Balance: {u['balance']} Tk\n👥 Referrals: {u['referrals']}")

@bot.message_handler(func=lambda message: message.text == "Wallet 💰")
def wallet_info(message):
    u = user_data.get(message.from_user.id, {"balance": 0.0})
    bot.send_message(message.chat.id, f"💰 **Wallet Balance:** {u['balance']} Tk")

# ----------------- TASK SYSTEM -----------------
@bot.message_handler(func=lambda message: message.text == "Task 📝")
def show_tasks(message):
    user_id = message.from_user.id
    init_user(user_id)
    markup = types.InlineKeyboardMarkup()
    
    for task in tasks_list:
        status = "✅ Done" if task['id'] in user_data[user_id]['completed_tasks'] else "📌"
        markup.add(types.InlineKeyboardButton(f"{status} {task['desc']} ({task['reward']} Tk)", callback_data=f"view_task:{task['id']}"))
    
    bot.send_message(message.chat.id, "🎯 **Available Tasks:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_task:"))
def view_task_callback(call):
    user_id = call.from_user.id
    init_user(user_id)
    task_id = int(call.data.split(":")[1])
    
    if task_id in user_data[user_id]['completed_tasks']:
        bot.answer_callback_query(call.id, "❌ You have already completed this task!", show_alert=True)
        return

    task = next((t for t in tasks_list if t['id'] == task_id), None)
    if task:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Open Link", url=task['link']),
                   types.InlineKeyboardButton("📤 Upload Proof", callback_data=f"upload_proof:{task_id}"))
        bot.send_message(call.message.chat.id, f"🎯 **{task['desc']}**\n💰 Reward: {task['reward']} Tk\n\nকাজটি সম্পন্ন করে স্ক্রিনশট দিন।", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_proof:"))
def prompt_proof(call):
    task_id = int(call.data.split(":")[1])
    user_data[call.from_user.id]['temp_task_id'] = task_id
    user_states[call.from_user.id] = 'waiting_for_task_proof'
    bot.send_message(call.message.chat.id, "📸 কাজের স্ক্রিনশটটি এখানে পাঠান:")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'waiting_for_task_proof':
        task_id = user_data[user_id]['temp_task_id']
        task = next((t for t in tasks_list if t['id'] == task_id), None)
        
        # প্রুফ লিস্টে যুক্ত করা
        proof_data = {
            "user_id": user_id,
            "user_name": message.from_user.first_name,
            "task_id": task_id,
            "photo_id": message.photo[-1].file_id,
            "task_name": task['desc'] if task else "Task",
            "reward": task['reward'] if task else 0.0
        }
        task_proofs.append(proof_data)
        
        bot.send_message(message.chat.id, "✅ আপনার প্রুফ সফলভাবে জমা হয়েছে! অ্যাডমিন যাচাই করে এপ্রুভ করবেন।")
        del user_states[user_id]

# ----------------- WITHDRAW SYSTEM -----------------
@bot.message_handler(func=lambda message: message.text == "Withdraw 💳")
def withdraw_req(message):
    user_id = message.from_user.id
    init_user(user_id)
    if user_data[user_id]['balance'] < 20:
        bot.send_message(message.chat.id, "❌ আপনার ব্যালেন্স ন্যূনতম ২০ টাকা হতে হবে।")
        return
    user_states[user_id] = 'waiting_for_withdraw_number'
    bot.send_message(message.chat.id, "💳 আপনার বিকাশ/নগদ নম্বর পাঠান:")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == 'waiting_for_withdraw_number')
def process_withdraw(message):
    user_id = message.from_user.id
    amount = user_data[user_id]['balance']
    withdraw_requests.append({"user_id": user_id, "name": message.from_user.first_name, "number": message.text, "amount": amount})
    user_data[user_id]['balance'] = 0.0
    bot.send_message(message.chat.id, "✅ উইথড্র রিকোয়েস্ট জমা হয়েছে!")
    del user_states[user_id]

# ----------------- ADMIN DASHBOARD (FOLDERS) -----------------
@bot.message_handler(commands=['admin'])
def admin_dashboard(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"💳 Withdrawals ({len(withdraw_requests)})", callback_data="admin_wd_list"),
        types.InlineKeyboardButton(f"📸 Task Proofs ({len(task_proofs)})", callback_data="admin_proof_list"),
        types.InlineKeyboardButton("⚙️ Manage Tasks", callback_data="admin_task_manage")
    )
    bot.send_message(ADMIN_ID, "👑 **Admin Dashboard**\nযেকোনো ফোল্ডার সিলেক্ট করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def admin_menu_handler(call):
    if call.data == "admin_task_manage":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add Task", callback_data="add_task_cmd"))
        bot.edit_message_text("⚙️ **Manage Tasks:**\n\nকমান্ড দিয়ে টাস্ক যুক্ত করতে পারবেন।", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    
    elif call.data == "admin_proof_list":
        if not task_proofs:
            bot.edit_message_text("📸 **Task Proofs:**\n\nবর্তমানে কোনো পেন্ডিং প্রুফ নেই।", chat_id=call.message.chat.id, message_id=call.message.message_id)
            return
        
        proof = task_proofs[0]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"app_p:{proof['user_id']}:{proof['task_id']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_p:{proof['user_id']}")
        )
        bot.send_photo(ADMIN_ID, proof['photo_id'], 
                       caption=f"📸 **New Task Proof!**\nUser: {proof['user_name']}\nTask: {proof['task_name']}\nReward: {proof['reward']} Tk", 
                       reply_markup=markup)
    
    elif call.data == "admin_wd_list":
        if not withdraw_requests:
            bot.edit_message_text("💳 **Withdrawals:**\n\nবর্তমানে কোনো পেন্ডিং উইথড্র রিকোয়েস্ট নেই।", chat_id=call.message.chat.id, message_id=call.message.message_id)
            return
        
        wd = withdraw_requests[0]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve Paid", callback_data=f"app_wd:{wd['user_id']}:{wd['amount']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_wd:{wd['user_id']}")
        )
        bot.send_message(ADMIN_ID, f"💳 **Withdraw Request:**\nUser: {wd['name']}\nNumber: {wd['number']}\nAmount: {wd['amount']} Tk", reply_markup=markup)

# ----------------- APPROVAL HANDLERS -----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("app_p:"))
def approve_proof(call):
    _, user_id, task_id = call.data.split(":")
    user_id, task_id = int(user_id), int(task_id)
    
    task = next((t for t in tasks_list if t['id'] == task_id), None)
    reward = task['reward'] if task else 0.0
    
    init_user(user_id)
    user_data[user_id]['balance'] += reward
    user_data[user_id]['completed_tasks'].append(task_id)
    
    # প্রুফ রিমুভ
    global task_proofs
    task_proofs = [p for p in task_proofs if not (p['user_id'] == user_id and p['task_id'] == task_id)]
    
    bot.send_message(user_id, f"🎉 অভিনন্দন! আপনার জমা দেওয়া টাস্ক এপ্রুভ হয়েছে। {reward} Tk যুক্ত করা হয়েছে।")
    bot.edit_message_caption("✅ Task Approved!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_wd:"))
def approve_wd(call):
    _, user_id, amount = call.data.split(":")
    
    global withdraw_requests
    withdraw_requests = [w for w in withdraw_requests if str(w['user_id']) != str(user_id)]
    
    bot.send_message(int(user_id), f"🎉 আপনার {amount} টাকা উইথড্র রিকোয়েস্ট এপ্রুভ হয়েছে এবং পেমেন্ট সম্পন্ন হয়েছে!")
    bot.edit_message_text("✅ Withdrawal Approved & Paid!", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == '__main__':
    bot.polling(none_stop=True)