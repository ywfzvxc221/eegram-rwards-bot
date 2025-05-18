import os import telebot from telebot import types from datetime import datetime, timedelta import json

API_TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not API_TOKEN or not ADMIN_ID: raise Exception("يرجى تحديد متغيرات BOT_TOKEN و ADMIN_ID في البيئة")

bot = telebot.TeleBot(API_TOKEN)

users = {} user_withdraw_data = {} daily_bonus_time = {}

@bot.message_handler(commands=['start']) def send_start(message): user_id = message.chat.id if user_id not in users: users[user_id] = {"balance": 0, "referrals": []} markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.row( types.KeyboardButton("💰 الرصيد"), types.KeyboardButton("🎁 المكافأة اليومية") ) markup.row( types.KeyboardButton("👥 دعوة الأصدقاء"), types.KeyboardButton("💸 سحب الأرباح") ) bot.send_message(user_id, "مرحبًا بك في البوت الربحي! اختر من القائمة:", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "💰 الرصيد") def show_balance(message): user_id = message.chat.id balance = users.get(user_id, {}).get("balance", 0) bot.send_message(user_id, f"رصيدك الحالي: {balance} دولار")

@bot.message_handler(func=lambda msg: msg.text == "🎁 المكافأة اليومية") def daily_bonus(message): user_id = message.chat.id now = datetime.now() if user_id not in daily_bonus_time or now > daily_bonus_time[user_id]: users[user_id]["balance"] += 0.01 daily_bonus_time[user_id] = now + timedelta(hours=24) bot.send_message(user_id, "✅ تم إضافة 0.01 دولار إلى رصيدك كمكافأة يومية.") else: time_left = daily_bonus_time[user_id] - now bot.send_message(user_id, f"⏳ لقد حصلت على مكافأتك اليومية.\nجرب مرة أخرى بعد {str(time_left).split('.')[0]}")

@bot.message_handler(func=lambda msg: msg.text == "👥 دعوة الأصدقاء") def invite_friends(message): user_id = message.chat.id referral_link = f"https://t.me/اسم_البوت?start={user_id}" bot.send_message(user_id, f"قم بدعوة أصدقائك باستخدام هذا الرابط:\n{referral_link}")

@bot.message_handler(func=lambda message: message.text == "💸 سحب الأرباح") def choose_withdraw_method(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) methods = [ "الكريمي 🇾🇪", "فودافون كاش 🇪🇬", "شركة النجم للصرافة 🇾🇪", "شركة القطيبي للصرافة 🇾🇪", "الاهلي 🇸🇦", "الراجحي 🇸🇦", "بيبال 🇲🇦", "بنك CIH 🇲🇦", "بنك الاردن 🇯🇴", "زين كاش 🇮🇶", "محفظة Ooredoo 🇶🇦", "محفظة Jawwal 🇵🇸", "بنك لبنان والمهجر 🇱🇧" ] for i in range(0, len(methods), 2): markup.row(*[types.KeyboardButton(method) for method in methods[i:i+2]]) markup.row(types.KeyboardButton("⬅️ العودة")) bot.send_message(message.chat.id, "اختر طريقة السحب المناسبة لك:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in [ "الكريمي 🇾🇪", "فودافون كاش 🇪🇬", "شركة النجم للصرافة 🇾🇪", "شركة القطيبي للصرافة 🇾🇪", "الاهلي 🇸🇦", "الراجحي 🇸🇦", "بيبال 🇲🇦", "بنك CIH 🇲🇦", "بنك الاردن 🇯🇴", "زين كاش 🇮🇶", "محفظة Ooredoo 🇶🇦", "محفظة Jawwal 🇵🇸", "بنك لبنان والمهجر 🇱🇧" ]) def ask_amount(message): user_id = message.chat.id user_withdraw_data[user_id] = {"method": message.text} bot.send_message(user_id, "يرجى إرسال المبلغ المراد سحبه:")

@bot.message_handler(func=lambda message: message.chat.id in user_withdraw_data and "amount" not in user_withdraw_data[message.chat.id]) def ask_info(message): user_id = message.chat.id user_withdraw_data[user_id]["amount"] = message.text bot.send_message(user_id, "يرجى إرسال معلومات السحب:\nالاسم الكامل\nرقم الهاتف\nطريقة السحب")

@bot.message_handler(func=lambda message: message.chat.id in user_withdraw_data and "info" not in user_withdraw_data[message.chat.id]) def confirm_data(message): user_id = message.chat.id user_withdraw_data[user_id]["info"] = message.text data = user_withdraw_data[user_id] summary = f"""هل هذه هي معلومات السحب الصحيحة؟\n\nالمبلغ: {data['amount']}\nطريقة السحب: {data['method']}\nالمعلومات:\n{data['info']}\n\nالحد الأدنى للسحب هو 0.0001 بيتكوين""" markup = types.InlineKeyboardMarkup() markup.add( types.InlineKeyboardButton("✅ تأكيد السحب", callback_data="confirm_withdraw"), types.InlineKeyboardButton("❌ إلغاء السحب", callback_data="cancel_withdraw") ) bot.send_message(user_id, summary, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_withdraw", "cancel_withdraw"]) def handle_withdraw_choice(call): user_id = call.message.chat.id if call.data == "confirm_withdraw": bot.send_message(user_id, "✅ تم تأكيد السحب. سيتم مراجعته من قبل الأدمن.") data = user_withdraw_data[user_id] withdraw_entry = { "user_id": user_id, "amount": data["amount"], "method": data["method"], "info": data["info"], "status": "قيد المراجعة", "timestamp": datetime.now().isoformat() } if os.path.exists("withdraw_requests.json"): with open("withdraw_requests.json", "r") as f: existing = json.load(f) else: existing = [] existing.append(withdraw_entry) with open("withdraw_requests.json", "w") as f: json.dump(existing, f, ensure_ascii=False, indent=2)

admin_msg = f"🔔 طلب سحب جديد من المستخدم {user_id}:\nالمبلغ: {data['amount']}\nطريقة السحب: {data['method']}\nالمعلومات:\n{data['info']}"
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ قبول السحب", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ رفض السحب", callback_data=f"reject_{user_id}")
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)
else:
    bot.send_message(user_id, "❌ تم إلغاء عملية السحب.")
user_withdraw_data.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_")) def handle_admin_action(call): action, user_id_str = call.data.split("_") user_id = int(user_id_str) if os.path.exists("withdraw_requests.json"): with open("withdraw_requests.json", "r") as f: data = json.load(f) for entry in data: if entry["user_id"] == user_id: entry["status"] = "مقبول" if action == "approve" else "مرفوض" break with open("withdraw_requests.json", "w") as f: json.dump(data, f, ensure_ascii=False, indent=2) if action == "approve": bot.send_message(user_id, "✅ تم قبول طلب السحب الخاص بك. سيتم التنفيذ قريبًا.") bot.send_message(call.message.chat.id, f"تم قبول طلب السحب للمستخدم {user_id}.") else: bot.send_message(user_id, "❌ تم رفض طلب السحب الخاص بك.") bot.send_message(call.message.chat.id, f"تم رفض طلب السحب للمستخدم {user_id}.")

print("البوت يعمل...") bot.infinity_polling()

