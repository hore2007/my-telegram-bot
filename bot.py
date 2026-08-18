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
ADMIN_ID = 7989323715
BOT_USERNAME = "Hklucludxkhxtncdedugx_Bot"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# Data Stores
user_data = {}
user_states = {}
tasks_list = []
withdraw_requests = []
task_proofs = []
temp_task_data = {}
withdraw_temp = {}

def init_user(user_id, referrer_id=None):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 0.0,
            "referrals": 0,
            "referred_by": referrer_id,
            "completed_tasks": [],
            "temp_task_id": None
        }
        if referrer_id and referrer_id in user_data and referrer_id != user_id:
            user_data[referrer_id]['balance'] += 5.0
            user_data[referrer_id]['referrals'] += 1
            try:
                bot.send_message(referrer_id, "🎉 কেউ আপনার লিংকে জয়েন করেছে! আপনি ৫.০ টাকা রেফার বোনাস পেয়েছেন।")
            except:
                pass

def clear_admin_state():
    if ADMIN_ID in user_states:
        del user_states[ADMIN_ID]
    if ADMIN_ID in temp_task_data:
        del temp_task_data[ADMIN_ID]

# ----------------- KEYBOARDS -----------------
def get_user_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Account 👤", "Task 📝", "Wallet 💰", "Withdraw 💳", "Invite 📩", "Channel 📢")
    markup.add("Support Center 👥")
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Task Adder ➕", "Manage Tasks 🗑️", "Withdrawal 💳", "Task Approved 📸")
    markup.add("User Info 👥")
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add("❌ Cancel Task Add")
    return markup

# ----------------- START COMMAND -----------------
@bot.message_handler(commands=['start', 'admin'])
def start_cmd(message):
    user_id = message.from_user.id
    clear_admin_state()
    
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
        except ValueError:
            referrer_id = None
        
    init_user(user_id, referrer_id)
    
    if user_id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 **Admin Panel Activated!**", parse_mode="Markdown", reply_markup=get_admin_menu())
    else:
        bot.send_message(message.chat.id, f"👋 **Welcome {message.from_user.first_name}!**\n\nAppEarnBD বোটে আপনাকে স্বাগতম। কাজ করে আয় করা শুরু করুন!", parse_mode="Markdown", reply_markup=get_user_menu())

# =================================================
# 👑 ADMIN INTERFACE LOGIC
# =================================================

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "❌ Cancel Task Add")
def cancel_task_add(message):
    clear_admin_state()
    bot.send_message(ADMIN_ID, "🚫 টাস্ক যোগ করার প্রক্রিয়া বাতিল করা হয়েছে।", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "User Info 👥")
def admin_user_info(message):
    total_users = len(user_data)
    
    if not user_data:
        msg = "👥 **Total Members:** 0\n\nকোনো মেম্বার পাওয়া যায়নি।"
    else:
        msg = f"👥 **Total Members:** {total_users}\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"
        for uid, info in user_data.items():
            completed_count = len(info.get('completed_tasks', []))
            msg += (
                f"👤 **User ID:** `{uid}`\n"
                f"💰 **Balance:** {info['balance']} Tk\n"
                f"👥 **Referrals:** {info['referrals']}\n"
                f"✅ **Completed Tasks:** {completed_count}\n"
                f"-----------------------------------\n"
            )
            
    bot.send_message(ADMIN_ID, msg, parse_mode="Markdown", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Task Adder ➕")
def start_add_task(message):
    clear_admin_state()
    user_states[ADMIN_ID] = 'waiting_task_desc'
    bot.send_message(ADMIN_ID, "📝 **Step 1:** টাস্কের বিবরণ/নাম লিখুন:", parse_mode="Markdown", reply_markup=get_cancel_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Manage Tasks 🗑️")
def manage_tasks(message):
    if not tasks_list:
        bot.send_message(ADMIN_ID, "❌ বর্তমানে কোনো টাস্ক নেই।", reply_markup=get_admin_menu())
        return
    
    markup = types.InlineKeyboardMarkup()
    for task in tasks_list:
        markup.add(types.InlineKeyboardButton(f"🗑️ Delete: {task['desc']} ({task['reward']} Tk)", callback_data=f"del_task:{task['id']}"))
    bot.send_message(ADMIN_ID, "🗑️ ডিলেট করার জন্য টাস্কের ওপর ক্লিক করুন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_task:"))
def delete_task_callback(call):
    if call.from_user.id == ADMIN_ID:
        task_id = int(call.data.split(":")[1])
        global tasks_list
        tasks_list = [t for t in tasks_list if t['id'] != task_id]
        bot.answer_callback_query(call.id, "✅ টাস্কটি সফলভাবে ডিলেট করা হয়েছে!", show_alert=True)
        bot.edit_message_text("✅ টাস্কটি সফলভাবে ডিলেট করা হয়েছে!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Withdrawal 💳")
def admin_withdrawals(message):
    if not withdraw_requests:
        bot.send_message(ADMIN_ID, "💳 **Withdrawal Section:**\n\nবর্তমানে কোনো পেন্ডিং উইথড্র নেই।", parse_mode="Markdown", reply_markup=get_admin_menu())
        return
    
    for wd in withdraw_requests:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve Paid", callback_data=f"app_wd:{wd['user_id']}:{wd['amount']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_wd:{wd['user_id']}:{wd['amount']}")
        )
        bot.send_message(ADMIN_ID, f"💳 **Pending Request:**\n\n👤 User ID: `{wd['user_id']}`\n🏷️ Name: {wd['name']}\n🏦 Method: **{wd['method']}**\n📱 Number: `{wd['number']}`\n💰 Amount: **{wd['amount']} Tk**", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text == "Task Approved 📸")
def admin_task_proofs(message):
    if not task_proofs:
        bot.send_message(ADMIN_ID, "📸 **Task Approved Section:**\n\nবর্তমানে কোনো পেন্ডিং প্রুফ নেই।", parse_mode="Markdown", reply_markup=get_admin_menu())
        return
    
    for proof in task_proofs:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"app_p:{proof['user_id']}:{proof['task_id']}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_p:{proof['user_id']}:{proof['task_id']}")
        )
        bot.send_photo(ADMIN_ID, proof['photo_id'], 
                       caption=f"📸 **Submitted Proof:**\n\n👤 User ID: `{proof['user_id']}`\n🏷️ User: {proof['user_name']}\n📌 Task: {proof['task_name']}\n💰 Price: {proof['reward']} Tk", 
                       parse_mode="Markdown", reply_markup=markup)

# Admin Dynamic Task Inputs
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID) == 'waiting_task_desc')
def get_task_desc(message):
    temp_task_data[ADMIN_ID] = {'desc': message.text}
    user_states[ADMIN_ID] = 'waiting_task_link'
    bot.send_message(ADMIN_ID, "🔗 **Step 2:** টাস্কের লিংকটি লিখুন:", parse_mode="Markdown", reply_markup=get_cancel_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID) == 'waiting_task_link')
def get_task_link(message):
    temp_task_data[ADMIN_ID]['link'] = message.text
    user_states[ADMIN_ID] = 'waiting_task_reward'
    bot.send_message(ADMIN_ID, "💰 **Step 3:** টাস্কের প্রাইস কত টাকা হবে? (যেমন: 5.0):", parse_mode="Markdown", reply_markup=get_cancel_menu())

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and user_states.get(ADMIN_ID) == 'waiting_task_reward')
def get_task_reward(message):
    try:
        reward = float(message.text)
        new_id = len(tasks_list) + 100
        new_task = {
            "id": new_id,
            "desc": temp_task_data[ADMIN_ID]['desc'],
            "link": temp_task_data[ADMIN_ID]['link'],
            "reward": reward
        }
        tasks_list.append(new_task)
        clear_admin_state()
        bot.send_message(ADMIN_ID, f"✅ **Task Added Successfully!**\n\n📌 Task: {new_task['desc']}\n💰 Price: {new_task['reward']} Tk", parse_mode="Markdown", reply_markup=get_admin_menu())
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট! শুধু সংখ্যা লিখুন (যেমন: 5.0):", reply_markup=get_cancel_menu())

# =================================================
# 👤 USER INTERFACE LOGIC
# =================================================

@bot.message_handler(func=lambda m: m.text == "Account 👤")
def account_info(message):
    init_user(message.from_user.id)
    u = user_data[message.from_user.id]
    completed_count = len(u.get('completed_tasks', []))
    
    msg = (
        "👤 **━━━ USER ACCOUNT INFO ━━━**\n\n"
        f"🆔 **User ID:** `{message.from_user.id}`\n"
        f"🏷️ **Name:** {message.from_user.first_name}\n\n"
        f"💰 **Current Balance:** `{u['balance']} Tk`\n"
        f"👥 **Total Referrals:** `{u['referrals']}`\n"
        f"✅ **Completed Tasks:** `{completed_count}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Wallet 💰")
def wallet_info(message):
    init_user(message.from_user.id)
    u = user_data[message.from_user.id]
    
    msg = (
        "💳 **━━━ WALLET BALANCE ━━━**\n\n"
        f"💰 **Main Balance:** `{u['balance']} Tk`\n"
        f"📌 **Minimum Withdraw:** `10.0 Tk`\n\n"
        "⚡ টাকা তুলতে 'Withdraw 💳' অপশনে চাপ দিন।"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Invite 📩")
def invite_info(message):
    user_id = message.from_user.id
    init_user(user_id)
    invite_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    msg = (
        "📩 **━━━ REFER & EARN ━━━**\n\n"
        "আপনার রেফারেল লিংক ব্যবহার করে বন্ধুদের ইনভাইট করুন এবং আয় বাড়ান!\n\n"
        f"🔗 **আপনার লিংক:**\n`{invite_link}`\n\n"
        "🎁 **বোনাস সুবিধা:**\n"
        "• প্রতি সফল রেফারে: **৫.০ টাকা**\n"
        "• লাইফটাইম রেফার কমিশন: **২০%**"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Channel 📢")
def channel_info(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel Now", url="https://t.me/AppEarnBD_official"))
    
    msg = (
        "📢 **━━━ OFFICIAL CHANNEL ━━━**\n\n"
        "আমাদের অফিসিয়াল টেলিগ্রাম চ্যানেলে যুক্ত থাকুন। নতুন কাজের আপডেট এবং পেমেন্ট প্রুফ এখানেই পাবেন!"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Support Center 👥")
def support_info(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎧 Contact Admin", url="https://t.me/AppEarnBD"))
    
    msg = (
        "🎧 **━━━ SUPPORT CENTER ━━━**\n\n"
        "আপনার কোনো প্রশ্ন, সমস্যা বা পেমেন্ট সংক্রান্ত তথ্য জানতে সরাসরি এডমিনের সাথে কথা বলুন।"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Task 📝")
def show_tasks(message):
    user_id = message.from_user.id
    init_user(user_id)
    
    if not tasks_list:
        bot.send_message(message.chat.id, "🎯 **বর্তমানে কোনো টাস্ক উপলব্ধ নেই।**", parse_mode="Markdown")
        return

    markup = types.InlineKeyboardMarkup()
    for task in tasks_list:
        status = "✅ Done" if task['id'] in user_data[user_id]['completed_tasks'] else "📌"
        markup.add(types.InlineKeyboardButton(f"{status} {task['desc']} ({task['reward']} Tk)", callback_data=f"view_task:{task['id']}"))
    bot.send_message(message.chat.id, "🎯 **Available Tasks:**\nনিচের কাজের ওপর ক্লিক করুন:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_task:"))
def view_task_callback(call):
    user_id = call.from_user.id
    init_user(user_id)
    task_id = int(call.data.split(":")[1])
    
    # Check if completed
    if task_id in user_data[user_id]['completed_tasks']:
        bot.answer_callback_query(call.id, "❌ আপনি এই টাস্কটি আগেই সম্পূর্ণ করেছেন!", show_alert=True)
        return

    # Check if proof is already pending
    already_submitted = any(p['user_id'] == user_id and p['task_id'] == task_id for p in task_proofs)
    if already_submitted:
        bot.answer_callback_query(call.id, "⏳ আপনি এই টাস্কের প্রুফ আগেই জমা দিয়েছেন এবং এটি অ্যাডমিন রিভিউতে আছে!", show_alert=True)
        return

    task = next((t for t in tasks_list if t['id'] == task_id), None)
    if task:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 Open Link", url=task['link']),
                   types.InlineKeyboardButton("📤 Upload Proof", callback_data=f"upload_proof:{task_id}"))
        bot.send_message(call.message.chat.id, f"🎯 **Task:** {task['desc']}\n💰 **Reward:** `{task['reward']} Tk`\n\nকাজটি শেষ করে স্ক্রিনশট পাঠাতে 'Upload Proof' বাটনে ক্লিক করুন।", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_proof:"))
def prompt_proof(call):
    user_id = call.from_user.id
    task_id = int(call.data.split(":")[1])
    
    already_submitted = any(p['user_id'] == user_id and p['task_id'] == task_id for p in task_proofs)
    if already_submitted:
        bot.answer_callback_query(call.id, "⏳ আপনি এই টাস্কের প্রুফ আগেই জমা দিয়েছেন!", show_alert=True)
        return
        
    user_data[user_id]['temp_task_id'] = task_id
    user_states[user_id] = 'waiting_for_task_proof'
    bot.send_message(call.message.chat.id, "📸 **আপনার সম্পন্ন করা কাজের স্ক্রিনশটটি এখানে পাঠান:**", parse_mode="Markdown")

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
        bot.send_message(message.chat.id, "✅ **আপনার প্রুফ জমা হয়েছে!**\nঅ্যাডমিন যাচাই করে খুব শীঘ্রই রিওয়ার্ড যুক্ত করে দেবেন।", parse_mode="Markdown")
        del user_states[user_id]

# ----------------- WITHDRAWAL FLOW -----------------
@bot.message_handler(func=lambda m: m.text == "Withdraw 💳")
def withdraw_req(message):
    user_id = message.from_user.id
    init_user(user_id)
    
    if user_data[user_id]['balance'] < 100.0:
        bot.send_message(message.chat.id, "❌ **উইথড্র করতে পারবেন না!**\n\nআপনার ব্যালেন্স ন্যূনতম **১০০ টাকা** হতে হবে।", parse_mode="Markdown")
        return
        
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("বিকাশ (bKash)", callback_data="wd_method:bKash"),
        types.InlineKeyboardButton("নগদ (Nagad)", callback_data="wd_method:Nagad")
    )
    bot.send_message(message.chat.id, "💳 **পেমেন্ট গ্রহণের মাধ্যম নির্বাচন করুন:**", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_method:"))
def select_withdraw_method(call):
    user_id = call.from_user.id
    method = call.data.split(":")[1]
    withdraw_temp[user_id] = {"method": method}
    user_states[user_id] = 'waiting_for_withdraw_amount'
    
    bot.edit_message_text(f"✅ **{method}** সিলেক্ট করা হয়েছে।\n\n💰 **কত টাকা উইথড্র দিতে চান তা লিখুন:** (আপনার ব্যালেন্স: {user_data[user_id]['balance']} Tk)", 
                          chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_for_withdraw_amount')
def process_withdraw_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)
        if amount < 100.0:
            bot.send_message(message.chat.id, "❌ ন্যূনতম উইথড্র পরিমাণ ১০০ টাকা। পুনরায় সঠিক অ্যামাউন্ট লিখুন:")
            return
        if amount > user_data[user_id]['balance']:
            bot.send_message(message.chat.id, f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! বর্তমান ব্যালেন্স: {user_data[user_id]['balance']} Tk\nপুনরায় পরিমাণ লিখুন:")
            return
            
        withdraw_temp[user_id]['amount'] = amount
        user_states[user_id] = 'waiting_for_withdraw_number'
        bot.send_message(message.chat.id, f"📱 **আপনার {withdraw_temp[user_id]['method']} নাম্বারটি লিখুন:**", parse_mode="Markdown")
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট! শুধু সংখ্যা লিখুন (যেমন: 50):")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_for_withdraw_number')
def process_withdraw_number(message):
    user_id = message.from_user.id
    number = message.text
    method = withdraw_temp[user_id]['method']
    amount = withdraw_temp[user_id]['amount']
    
    # Deduct balance
    user_data[user_id]['balance'] -= amount
    
    withdraw_requests.append({
        "user_id": user_id, 
        "name": message.from_user.first_name, 
        "method": method,
        "number": number, 
        "amount": amount
    })
    
    bot.send_message(message.chat.id, f"✅ **আপনার উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে!**\n\n🏦 Method: {method}\n📱 Number: {number}\n💰 Amount: {amount} Tk", parse_mode="Markdown")
    
    del user_states[user_id]
    if user_id in withdraw_temp:
        del withdraw_temp[user_id]

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
    
    bot.send_message(user_id, f"🎉 **অভিনন্দন!** আপনার জমা দেওয়া টাস্ক এপ্রুভ হয়েছে। **{reward} Tk** যুক্ত করা হয়েছে।", parse_mode="Markdown")
    bot.edit_message_caption("✅ Task Approved!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rej_p:"))
def reject_proof(call):
    _, user_id, task_id = call.data.split(":")
    user_id, task_id = int(user_id), int(task_id)
    
    global task_proofs
    task_proofs = [p for p in task_proofs if not (p['user_id'] == user_id and p['task_id'] == task_id)]
    
    bot.send_message(user_id, "❌ **আপনার জমা দেওয়া টাস্ক প্রুফটি বাতিল করা হয়েছে।**", parse_mode="Markdown")
    bot.edit_message_caption("❌ Task Rejected!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("app_wd:"))
def approve_wd(call):
    _, user_id, amount = call.data.split(":")
    global withdraw_requests
    withdraw_requests = [w for w in withdraw_requests if str(w['user_id']) != str(user_id)]
    
    bot.send_message(int(user_id), f"🎉 **আপনার {amount} টাকা উইথড্র রিকোয়েস্ট সফল হয়েছে!**", parse_mode="Markdown")
    bot.edit_message_text("✅ Withdrawal Approved & Paid!", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rej_wd:"))
def reject_wd(call):
    _, user_id, amount = call.data.split(":")
    user_id = int(user_id)
    amount = float(amount)
    
    # Refund balance on rejection
    init_user(user_id)
    user_data[user_id]['balance'] += amount
    
    global withdraw_requests
    withdraw_requests = [w for w in withdraw_requests if str(w['user_id']) != str(user_id)]
    
    bot.send_message(user_id, f"❌ **আপনার {amount} টাকা উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে।**\nটাকা পুনরায় আপনার ব্যালেন্সে যুক্ত করা হয়েছে।", parse_mode="Markdown")
    bot.edit_message_text("❌ Withdrawal Rejected & Refunded!", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == '__main__':
    bot.polling(none_stop=True)