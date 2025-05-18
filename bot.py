import os import telebot from telebot import types from datetime import datetime, timedelta import json

API_TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = os.getenv("ADMIN_ID")

if not API_TOKEN or not ADMIN_ID: raise Exception("يرجى تحديد متغيرات BOT_TOKEN و ADMIN_ID")

ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(API_TOKEN)

users = {} user_withdraw_data = {} daily_bonus_time = {} custom_welcome = "مرحبًا بك في البوت الربحي! اختر من القائمة:" admin_buttons = [] referral_bonus = 0.01 daily_bonus_amount = 0.01

@bot.message_handler(commands=['start']) def send_start(message): user_id = message.chat.id if user_id not in users: users[user_id] = {"balance": 0, "referrals": []} if message.text.startswith("/start "): ref_id = message.text.split()[1] if ref_id.isdigit() and int(ref_id) != user_id: ref_id = int(ref_id) if user_id not in users[ref_id]["referrals"]: users[ref_id]["balance"] += referral_bonus users[ref_id]["referrals"].append(user_id) markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.row(types.KeyboardButton("💰 الرصيد"), types.KeyboardButton("🎁 المكافأة اليومية")) markup.row(types.KeyboardButton("👥 دعوة الأصدقاء"), types.KeyboardButton("💸 سحب الأرباح")) for btn in admin_buttons: markup.row(types.KeyboardButton(btn)) if user_id == ADMIN_ID: markup.row(types.KeyboardButton("⚙️ لوحة التحكم")) bot.send_message(user_id, custom_welcome, reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "💰 الرصيد") def show_balance(message): balance = users.get(message.chat.id, {}).get("balance", 0) bot.send_message(message.chat.id, f"رصيدك الحالي: {balance:.2f} دولار")

@bot.message_handler(func=lambda msg: msg.text == "🎁 المكافأة اليومية") def daily_bonus(message): user_id = message.chat.id now = datetime.now() if user_id not in daily_bonus_time or now > daily_bonus_time[user_id]: users[user_id]["balance"] += daily_bonus_amount daily_bonus_time[user_id] = now + timedelta(hours=24) bot.send_message(user_id, f"✅ تم إضافة {daily_bonus_amount:.2f} دولار إلى رصيدك كمكافأة يومية.") else: time_left = daily_bonus_time[user_id] - now bot.send_message(user_id, f"⏳ جرب مرة أخرى بعد {str(time_left).split('.')[0]}")

@bot.message_handler(func=lambda msg: msg.text == "👥 دعوة الأصدقاء") def invite_friends(message): uid = message.chat.id link = f"https://t.me/{bot.get_me().username}?start={uid}" bot.send_message(uid, f"قم بدعوة أصدقائك عبر الرابط التالي واحصل على {referral_bonus:.2f} دولار عن كل إحالة:\n{link}")

@bot.message_handler(func=lambda msg: msg.text == "⚙️ لوحة التحكم" and msg.chat.id == ADMIN_ID) def admin_panel(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.row("➕ إضافة زر", "➖ حذف زر") markup.row("✏️ تعديل الترحيب", "🎁 تغيير مكافأة اليومية") markup.row("🎯 تغيير مكافأة الإحالة", "⬅️ رجوع") bot.send_message(message.chat.id, "مرحبًا بك في لوحة التحكم.", reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text == "➕ إضافة زر" and msg.chat.id == ADMIN_ID) def add_button(message): msg = bot.send_message(message.chat.id, "أرسل اسم الزر الجديد:") bot.register_next_step_handler(msg, lambda m: add_button_callback(m, message.chat.id))

def add_button_callback(m, admin_id): admin_buttons.append(m.text) bot.send_message(admin_id, f"✅ تم إضافة الزر '{m.text}' بنجاح.")

@bot.message_handler(func=lambda msg: msg.text == "➖ حذف زر" and msg.chat.id == ADMIN_ID) def remove_button(message): msg = bot.send_message(message.chat.id, "أرسل اسم الزر الذي تريد حذفه:") bot.register_next_step_handler(msg, lambda m: remove_button_callback(m, message.chat.id))

def remove_button_callback(m, admin_id): if m.text in admin_buttons: admin_buttons.remove(m.text) bot.send_message(admin_id, f"✅ تم حذف الزر '{m.text}' بنجاح.") else: bot.send_message(admin_id, "❌ هذا الزر غير موجود.")

@bot.message_handler(func=lambda msg: msg.text == "✏️ تعديل الترحيب" and msg.chat.id == ADMIN_ID) def update_welcome(message): msg = bot.send_message(message.chat.id, "أرسل رسالة الترحيب الجديدة:") bot.register_next_step_handler(msg, lambda m: save_welcome_callback(m, message.chat.id))

def save_welcome_callback(m, admin_id): global custom_welcome custom_welcome = m.text bot.send_message(admin_id, "✅ تم تحديث رسالة الترحيب.")

@bot.message_handler(func=lambda msg: msg.text == "🎯 تغيير مكافأة الإحالة" and msg.chat.id == ADMIN_ID) def update_ref_bonus(message): msg = bot.send_message(message.chat.id, f"المكافأة الحالية: {referral_bonus:.2f} دولار\nأرسل المكافأة الجديدة:") bot.register_next_step_handler(msg, lambda m: set_ref_bonus(m, message.chat.id))

def set_ref_bonus(m, admin_id): global referral_bonus try: referral_bonus = float(m.text) bot.send_message(admin_id, f"✅ تم تحديث مكافأة الإحالة إلى {referral_bonus:.2f} دولار") except: bot.send_message(admin_id, "❌ قيمة غير صحيحة.")

@bot.message_handler(func=lambda msg: msg.text == "🎁 تغيير مكافأة اليومية" and msg.chat.id == ADMIN_ID) def update_daily_bonus(message): msg = bot.send_message(message.chat.id, f"المكافأة الحالية: {daily_bonus_amount:.2f} دولار\nأرسل القيمة الجديدة:") bot.register_next_step_handler(msg, lambda m: set_daily_bonus(m, message.chat.id))

def set_daily_bonus(m, admin_id): global daily_bonus_amount try: daily_bonus_amount = float(m.text) bot.send_message(admin_id, f"✅ تم تحديث المكافأة اليومية إلى {daily_bonus_amount:.2f} دولار") except: bot.send_message(admin_id, "❌ قيمة غير صحيحة.")

الأوامر الأخرى (السحب...) كما هي

print("✅ البوت يعمل الآن...") bot.infinity_polling()

