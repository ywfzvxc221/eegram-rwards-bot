import telebot from telebot import types import os import json from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = int(os.getenv("ADMIN_ID")) bot = telebot.TeleBot(BOT_TOKEN)

تحميل المستخدمين

USERS_FILE = "users.json" if os.path.exists(USERS_FILE): with open(USERS_FILE, "r") as f: users = json.load(f) else: users = {}

إعدادات المكافآت

SETTINGS_FILE = "settings.json" settings = { "ref_bonus": 0.00000050, "daily_bonus": 0.00000040, "min_withdraw": 0.00001 } if os.path.exists(SETTINGS_FILE): with open(SETTINGS_FILE, "r") as f: settings.update(json.load(f))

def save_users(): with open(USERS_FILE, "w") as f: json.dump(users, f)

def save_settings(): with open(SETTINGS_FILE, "w") as f: json.dump(settings, f)

def main_menu(): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add("🎁 المكافأة اليومية", "👥 رابط الإحالة") markup.add("💸 سحب الأرباح", "📊 إحصائياتي") return markup

@bot.message_handler(commands=['start']) def start(message): user_id = str(message.from_user.id) if user_id not in users: users[user_id] = { "balance": 0, "last_daily": "", "refs": [] } if len(message.text.split()) > 1: ref_id = message.text.split()[1] if ref_id != user_id and ref_id in users: if user_id not in users[ref_id]["refs"]: users[ref_id]["refs"].append(user_id) users[ref_id]["balance"] += settings["ref_bonus"] save_users() bot.send_message(message.chat.id, "مرحبًا بك في بوت ربح البيتكوين من الدعوات!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎁 المكافأة اليومية") def daily_bonus(message): user_id = str(message.from_user.id) now = datetime.now() last = users[user_id]["last_daily"] if last: last_time = datetime.strptime(last, "%Y-%m-%d") if now.date() == last_time.date(): bot.send_message(message.chat.id, "لقد حصلت على مكافأتك اليومية اليوم. عد غدًا!") return users[user_id]["balance"] += settings["daily_bonus"] users[user_id]["last_daily"] = now.strftime("%Y-%m-%d") save_users() bot.send_message(message.chat.id, f"تمت إضافة {settings['daily_bonus']} BTC إلى رصيدك اليومي!")

@bot.message_handler(func=lambda m: m.text == "👥 رابط الإحالة") def referral_link(message): user_id = message.from_user.id link = f"https://t.me/{bot.get_me().username}?start={user_id}" bot.send_message(message.chat.id, f"رابط الدعوة الخاص بك: {link}")

@bot.message_handler(func=lambda m: m.text == "📊 إحصائياتي") def my_stats(message): user_id = str(message.from_user.id) data = users.get(user_id, {}) refs = len(data.get("refs", [])) balance = data.get("balance", 0) bot.send_message(message.chat.id, f"رصيدك: {balance:.8f} BTC\nعدد الإحالات: {refs}")

@bot.message_handler(func=lambda m: m.text == "💸 سحب الأرباح") def withdraw(message): markup = types.InlineKeyboardMarkup() markup.add(types.InlineKeyboardButton("سحب عبر FaucetPay", callback_data="withdraw_faucetpay")) markup.add(types.InlineKeyboardButton("سحب عبر Binance", callback_data="withdraw_binance")) bot.send_message(message.chat.id, "اختر طريقة السحب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("withdraw_")) def process_withdraw_method(call): method = call.data.split("_")[1] bot.send_message(call.message.chat.id, f"أدخل {'البريد الإلكتروني لمحفظة FaucetPay' if method == 'faucetpay' else 'عنوان محفظة BTC على Binance'}:") bot.register_next_step_handler(call.message, process_withdraw_address, method)

def process_withdraw_address(message, method): user_id = str(message.from_user.id) address = message.text.strip() balance = users[user_id]["balance"] if balance < settings["min_withdraw"]: bot.send_message(message.chat.id, "❌ الحد الأدنى للسحب هو BTC 0.00001") return if method == "faucetpay": if "@" not in address: bot.send_message(message.chat.id, "❌ يرجى إدخال بريد إلكتروني صحيح لفوسيت باي.") return elif method == "binance": if len(address) < 25: bot.send_message(message.chat.id, "❌ يرجى إدخال عنوان محفظة Binance صحيح.") return users[user_id]["balance"] = 0 save_users() bot.send_message(message.chat.id, f"✅ تم استلام طلب السحب بنجاح! سيتم إرسال المبلغ إلى {address} خلال 24 ساعة.")

لوحة تحكم الأدمن

@bot.message_handler(commands=['admin']) def admin_panel(message): if message.from_user.id != ADMIN_ID: return markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add("📢 إرسال رسالة جماعية", "📈 إحصائيات البوت") markup.add("⚙️ تعديل المكافآت", "🔙 رجوع") bot.send_message(message.chat.id, "👨‍💻 لوحة تحكم الأدمن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 رجوع" and m.from_user.id == ADMIN_ID) def back_to_main(message): bot.send_message(message.chat.id, "تم الرجوع للقائمة.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📈 إحصائيات البوت" and m.from_user.id == ADMIN_ID) def bot_stats(message): total_users = len(users) total_refs = sum(len(u["refs"]) for u in users.values()) total_balance = sum(u["balance"] for u in users.values()) bot.send_message(message.chat.id, f"👥 المستخدمون: {total_users}\n🔁 الإحالات: {total_refs}\n💰 إجمالي الأرصدة: {total_balance:.8f} BTC")

@bot.message_handler(func=lambda m: m.text == "📢 إرسال رسالة جماعية" and m.from_user.id == ADMIN_ID) def broadcast_prompt(message): bot.send_message(message.chat.id, "📝 أرسل الآن الرسالة التي تريد إرسالها لكل المستخدمين:") bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message): count = 0 for user_id in users: try: bot.send_message(user_id, message.text) count += 1 except: continue bot.send_message(message.chat.id, f"✅ تم إرسال الرسالة إلى {count} مستخدم.")

@bot.message_handler(func=lambda m: m.text == "⚙️ تعديل المكافآت" and m.from_user.id == ADMIN_ID) def change_settings(message): bot.send_message(message.chat.id, f"⚙️ القيم الحالية:\n- مكافأة الإحالة: {settings['ref_bonus']} BTC\n- المكافأة اليومية: {settings['daily_bonus']} BTC\n- الحد الأدنى للسحب: {settings['min_withdraw']} BTC\n\n📝 أرسل القيم الجديدة بهذا الشكل:\n<إحالة>,<يومية>,<حد أدنى>\nمثال:\n0.00000030,0.00000020,0.00001") bot.register_next_step_handler(message, update_settings)

def update_settings(message): try: ref_bonus, daily_bonus, min_withdraw = map(float, message.text.strip().split(",")) settings["ref_bonus"] = ref_bonus settings["daily_bonus"] = daily_bonus settings["min_withdraw"] = min_withdraw save_settings() bot.send_message(message.chat.id, "✅ تم تحديث القيم بنجاح.") except: bot.send_message(message.chat.id, "❌ صيغة غير صحيحة. حاول مرة أخرى.")

bot.infinity_polling()

