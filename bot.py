import os
from flask import Flask
from threading import Thread
import telebot
from telebot import types

# ----------------- SERVER KEEP-ALIVE -----------------
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run).start()

# ----------------- CONFIGURATION -----------------
BOT_TOKEN = '8901853120:AAFWduGM0qe2zD3_HYvFicvBikF8ip3LCBE'
ADMIN_ID = 6784510011

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# Data Stores
user_data = {}
user_states = {}
tasks_list = [{"id": 1, "desc": "Join Channel", "link": "https://t.me/AppEarnBD", "reward": 5.0}]
withdraw_requests = []
task_proofs = []
temp_task_data = {}

def init_user(user_id, referrer_id=None):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "referrals": 0,
            "referred_by": referrer_id,
            "completed_tasks": [],
            "temp_task_id": None
        }
        # রেফার বোনাস দেওয়া (৫ টাকা)
        if referrer_id and referrer_id in user_data and referrer_id != user_id:
            user_data[referrer_id]['balance'] += 5.0
            user_data[referrer_id]['referrals'] += 1
            try:
                bot.send_message(referrer_id, "🎉 কেউ আপনার লিংকে জয়েন করেছে! আপনি ৫.০ টাকা বোনাস পেয়েছেন।")
            except:
                pass

# ----------------- KEYBOARDS -----------------
def get_user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Account 👤", "Task 📝", "Wallet 💰", "Withdraw 💳", "Invite 📩", "Channel 📢")
    markup.add("Support Center 👥")
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Task Adder ➕", "Withdrawal 💳", "Task Approved 📸", "User Info 👥")
    return markup

# ----------------- START COMMAND -----------------
@bot.message_handler(commands=['start', 'admin'])
def start_cmd(message):
    user_id = message.from_user.id
    
    # রেফারেল আইডি এক্সট্রাক্ট করা
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        
    init_user(user_id, referrer_id)
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 Admin Panel Activated!\nআপনার ইন্টারফেস:", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, f"👋 Welcome {message.from_user.first_name}!", reply_markup=get_user_menu())

# =================================================
# 👑 ADMIN INTERFACE LOGIC
# =================================================

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "User Info 👥")
def admin_user_info(message):
    total_users = len(user_data)
    user_ids_text = "\n".join([f"• {uid}" for uid in user_data.keys()]) if user_data else "কোনো মেম্বার নেই"
    msg = f"👥 Total Members: {total_users}\n\nUser IDs:\n{user_ids_text}"
    bot.send_message(ADMIN_ID, msg)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Task Adder ➕")
def start_add_task(message):
    user_states[ADMIN_ID] = 'waiting_task_desc'
    bot.send_message(ADMIN_ID, "📝 Step 1: টাস্কের বিবরণ/নাম লিখুন:")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID) == 'waiting_task_desc')
def get_task_desc(message):
    temp_task_data[ADMIN_ID] = {'desc': message.text}
    user_states[ADMIN_ID] = 'waiting_task_link'
    bot.send_message(ADMIN_ID, "🔗 Step 2: টাস্কের লিংকটি লিখুন:")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID) == 'waiting_task_link')
def get_task_link(message):
    temp_task_data[ADMIN_ID]['link'] = message.text
    user_states[ADMIN_ID] = 'waiting_task_reward'
    bot.send_message(ADMIN_ID, "💰 Step 3: টাস্কের প্রাইস কত টাকা হবে? (যেমন: 5.0):")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID) == 'waiting_task_reward')
def get_task_reward(message):
    try:
        reward = float(message.text)
        new_id = len(tasks_list) + 1
        new_task = {
            "id": new_id,
            "desc": temp_task_data[ADMIN_ID]['desc'],
            "link": temp_task_data[ADMIN_ID]['link'],
            "reward": reward
        }
        tasks_list.append(new_task)
        del user_states[ADMIN_ID]
        del temp_task_data[ADMIN_ID]
        bot.send_message(ADMIN_ID, f"✅ Task Added Successfully!\n\n📌 Task: {new_task['desc']}\n💰 Price: {new_task['reward']} Tk", reply_markup=get_admin_menu())
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট! শুধু সংখ্যা লিখুন (যেমন: 5.0):")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Withdrawal 💳")
def admin_withdrawals(message):
    if not withdraw_requests:
        bot.send_message(ADMIN_ID, "💳 Withdrawal Section:\n\nবর্তমানে কোনো পেন্ডিং উইথড্র নেই।")
        return
    
    for wd in withdraw_requests:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve Paid", callback_data=f"app_wd:{wd['user_id']}:{wd['amount']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_wd:{wd['user_id']}")
        )
        bot.send_message(ADMIN_ID, f"💳 Pending Request:\nUser ID: {wd['user_id']}\nName: {wd['name']}\nNumber: {wd['number']}\nAmount: {wd['amount']} Tk", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Task Approved 📸")
def admin_task_proofs(message):
    if not task_proofs:
        bot.send_message(ADMIN_ID, "📸 Task Approved Section:\n\nবর্তমানে কোনো পেন্ডিং প্রুফ নেই।")
        return
    
    for proof in task_proofs:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"app_p:{proof['user_id']}:{proof['task_id']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_p:{proof['user_id']}")
        )
        bot.send_photo(ADMIN_ID, proof['photo_id'], 
                       caption=f"📸 Submitted Proof:\nUser ID: {proof['user_id']}\nUser: {proof['user_name']}\nTask: {proof['task_name']}\nPrice: {proof['reward']} Tk", 
                       reply_markup=markup)

# =================================================
# 👤 USER INTERFACE LOGIC
# =================================================

@bot.message_handler(func=lambda m: m.text == "Account 👤")
def account_info(message):
    init_user(message.from_user.id)
    u = user_data[message.from_user.id]
    bot.send_message(message.chat.id, f"👤 Account Info\n\n💰 Balance: {u['balance']} Tk\n👥 Referrals: {u['referrals']}")

@bot.message_handler(func=lambda m: m.text == "Wallet 💰")
def wallet_info(message):
    init_user(message.from_user.id)
    u = user_data[message.from_user.id]
    bot.send_message(message.chat.id, f"💰 Wallet Balance: {u['balance']} Tk")

@bot.message_handler(func=lambda m: m.text == "Invite 📩")
def invite_info(message):
    bot.send_message(message.chat.id, f"📩 Invite Link:\nhttps://t.me/AppEarnBD_bot?start={message.from_user.id}\n\n🎉 প্রতি রেফারে পাবেন ৫.০ টাকা বোনাস এবং জীবনের সব উপার্জনের উপর ২০% লাইফটাইম কমিশন!")

@bot.message_handler(func=lambda m: m.text == "Channel 📢")
def channel_info(message):
    bot.send_message(message.chat.id, "📢 Join Channel: https://t.me/AppEarnBD")

@bot.message_handler(func=lambda m: m.text == "Support Center 👥")
def support_info(message):
    bot.send_message(message.chat.id, "🎧 Support Center:\nযেকোনো সমস্যায় অ্যাডমিনের সাথে যোগাযোগ করুন: @AppEarnBD_Admin")

@bot.message_handler(func=lambda m: m.text == "Task 📝")
def show_tasks(message):
    user_id = message.from_user.id
    init_user(user_id)
    markup = types.InlineKeyboardMarkup()
    for task in tasks_list:
        status = "✅ Done" if task['id'] in user_data[user_id]['completed_tasks'] else "📌"
        markup.add(types.InlineKeyboardButton(f"{status} {task['desc']} ({task['reward']} Tk)", callback_data=f"view_task:{task['id']}"))
    bot.send_message(message.chat.id, "🎯 Available Tasks:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_task:"))
def view_task_callback(call):
    user_id = call.from_user.id
    init_user(user_id)
    task_id = int(call.data.split(":")[1])
    
    if task_id in user_data[user_id]['completed_tasks']:
        bot.answer_callback_query(call.id, "❌ আপনি এই টাস্কটি আগেই সম্পূর্ণ করেছেন!", show_alert=True)
        return

    task = next((t for t in tasks_list if t['id'] == task_id), None)
    if task:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Open Link", url=task['link']),
                   types.InlineKeyboardButton("📤 Upload Proof", callback_data=f"upload_proof:{task_id}"))
        bot.send_message(call.message.chat.id, f"🎯 {task['desc']}\n💰 Reward: {task['reward']} Tk\n\nকাজটি শেষ করে স্ক্রিনশট দিন।", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_proof:"))
def prompt_proof(call):
    task_id = int(call.data.split(":")[1])
    user_data[call.from_user.id]['temp_task_id'] = task_id
    user_states[call.from_user.id] = 'waiting_for_task_proof'
    bot.send_message(call.message.chat.id, "📸 স্ক্রিনশটটি এখানে পাঠান:")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == 'waiting_for_task_proof':
        task_id = user_data[user_id]['temp_task_id']
        task = next((t for t in tasks_list if t['id'] == task_id), None)
        
        task_proofs.append({
            "user_id": user_id,
            "user_name": message.from_user.first_name,
            "task_id": task_id,
            "photo_id": message.photo[-1].file_id,
            "task_name": task['desc'] if task else "Task",
            "reward": task['reward'] if task else 0.0
        })
        bot.send_message(message.chat.id, "✅ আপনার প্রুফ জমা হয়েছে! অ্যাডমিন যাচাই করবেন।")
        del user_states[user_id]

# ----------------- WITHDRAWAL FLOW -----------------
@bot.message_handler(func=lambda m: m.text == "Withdraw 💳")
def withdraw_req(message):
    user_id = message.from_user.id
    init_user(user_id)
    if user_data[user_id]['balance'] < 100.0:
        bot.send_message(message.chat.id, "❌ আপনার ব্যালেন্স ন্যূনতম ১০০ টাকা হতে হবে।")
        return
    user_states[user_id] = 'waiting_for_withdraw_number'
    bot.send_message(message.chat.id, "💳 আপনার বিকাশ/নগদ নম্বর পাঠান:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_for_withdraw_number')
def process_withdraw(message):
    user_id = message.from_user.id
    amount = user_data[user_id]['balance']
    withdraw_requests.append({
        "user_id": user_id, 
        "name": message.from_user.first_name, 
        "number": message.text, 
        "amount": amount
    })
    user_data[user_id]['balance'] = 0.0
    bot.send_message(message.chat.id, "✅ উইথড্র রিকোয়েস্ট জমা হয়েছে!")
    del user_states[user_id]

# =================================================
# ⚙️ APPROVAL & COMMISSION LOGIC
# =================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_p:"))
def approve_proof(call):
    _, user_id, task_id = call.data.split(":")
    user_id, task_id = int(user_id), int(task_id)
    
    task = next((t for t in tasks_list if t['id'] == task_id), None)
    reward = task['reward'] if task else 0.0
    
    init_user(user_id)
    user_data[user_id]['balance'] += reward
    user_data[user_id]['completed_tasks'].append(task_id)
    
    # 🌟 ২০% লাইফটাইম রেফার কমিশন যোগ
    referrer_id = user_data[user_id].get('referred_by')
    if referrer_id and referrer_id in user_data:
        commission = reward * 0.20
        user_data[referrer_id]['balance'] += commission
        try:
            bot.send_message(referrer_id, f"🎉 আপনার রেফারের কাজের ২০% কমিশন ({commission} Tk) যোগ হয়েছে!")
        except:
            pass

    global task_proofs
    task_proofs = [p for p in task_proofs if not (p['user_id'] == user_id and p['task_id'] == task_id)]
    
    bot.send_message(user_id, f"🎉 অভিনন্দন! আপনার জমা দেওয়া টাস্ক এপ্রুভ হয়েছে। {reward} Tk যুক্ত করা হয়েছে।")
    bot.edit_message_caption("✅ Task Approved!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rej_p:"))
def reject_proof(call):
    user_id = int(call.data.split(":")[1])
    bot.send_message(user_id, "❌ আপনার জমা দেওয়া টাস্ক প্রুফটি বাতিল করা হয়েছে।")
    bot.edit_message_caption("❌ Task Rejected!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_wd:"))
def approve_wd(call):
    _, user_id, amount = call.data.split(":")
    global withdraw_requests
    withdraw_requests = [w for w in withdraw_requests if str(w['user_id']) != str(user_id)]
    
    bot.send_message(int(user_id), f"🎉 আপনার {amount} টাকা উইথড্র রিকোয়েস্ট সফল হয়েছে!")
    bot.edit_message_text("✅ Withdrawal Approved & Paid!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rej_wd:"))
def reject_wd(call):
    user_id = int(call.data.split(":")[1])
    global withdraw_requests
    withdraw_requests = [w for w in withdraw_requests if str(w['user_id']) != str(user_id)]
    
    bot.send_message(user_id, "❌ আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে।")
    bot.edit_message_text("❌ Withdrawal Rejected!", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == '__main__':
    bot.polling(none_stop=True)