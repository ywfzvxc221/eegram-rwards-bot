import telebot import json import os from datetime import datetime

قراءة التوكن وID الأدمن من متغيرات البيئة

BOT_TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = os.getenv("ADMIN_ID")  # تأكد أنه string عند المقارنة

bot = telebot.TeleBot(BOT_TOKEN)

تحميل المستخدمين

if not os.path.exists("users.json"): with open("users.json", "w") as f: json.dump({}, f)

with open("users.json", "r") as f: users = json.load(f)

حفظ المستخدمين

def save_data(): with open("users.json", "w") as f: json.dump(users, f, indent=4)

تخزين مؤقت للبيانات

user_data = {}

حفظ طلبات الرشق

def save_order(order): if not os.path.exists("orders.json"): with open("orders.json", "w") as f: json.dump([], f) with open("orders.json", "r") as f: orders = json.load(f) orders.append(order) with open("orders.json", "w") as f: json.dump(orders, f, indent=4)

/start لتسجيل المستخدم

@bot.message_handler(commands=["start"]) def start(message): user_id = str(message.from_user.id) if user_id not in users: users[user_id] = {"points": 10, "username": message.from_user.username or ""} save_data() bot.send_message(message.chat.id, "أهلاً بك! اختر من القائمة:", reply_markup=main_menu())

القائمة الرئيسية

def main_menu(): markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True) markup.row("رصيدي", "رشق قناتي") return markup

عرض الرصيد

@bot.message_handler(func=lambda message: message.text == "رصيدي") def show_points(message): user_id = str(message.from_user.id) points = users.get(user_id, {}).get("points", 0) bot.send_message(message.chat.id, f"رصيدك الحالي: {points} نقطة")

بدء الرشق

@bot.message_handler(func=lambda message: message.text == "رشق قناتي") def ask_link(message): user_id = str(message.from_user.id) if user_id not in users: return bot.send_message(message.chat.id, "يجب التسجيل أولاً عبر /start.") msg = bot.send_message(message.chat.id, "أرسل رابط القناة أو الحساب الذي تريد رشه:") bot.register_next_step_handler(msg, ask_amount)

def ask_amount(message): link = message.text if not link.startswith("http"): return bot.send_message(message.chat.id, "❌ الرابط غير صحيح. أعد المحاولة.") user_data[message.chat.id] = {"link": link} msg = bot.send_message(message.chat.id, "كمية الرشق المطلوبة؟ (مثال: 100)") bot.register_next_step_handler(msg, confirm_order)

def confirm_order(message): try: amount = int(message.text) if amount <= 0: raise ValueError except: return bot.send_message(message.chat.id, "❌ الكمية غير صحيحة. أعد المحاولة.")

user_id = str(message.from_user.id)
cost = amount // 10  # كل 10 متابعين = 1 نقطة
if users[user_id]['points'] < cost:
    return bot.send_message(message.chat.id, f"❌ ليس لديك نقاط كافية. السعر: {cost} نقطة.")

users[user_id]['points'] -= cost
save_data()

order = {
    "user_id": user_id,
    "username": message.from_user.username or "",
    "link": user_data[message.chat.id]["link"],
    "amount": amount,
    "cost": cost,
    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
save_order(order)

bot.send_message(message.chat.id, f"✅ تم استلام طلبك بنجاح!\nالرابط: {order['link']}\nالكمية: {amount}\nتم خصم {cost} نقطة.")
bot.send_message(ADMIN_ID, f"طلب رشق جديد:\nمن: @{order['username']}\nالرابط: {order['link']}\nالكمية: {amount}\nالنقاط المخصومة: {cost}")

عرض الطلبات للأدمن

@bot.message_handler(commands=["عرض_الطلبات"]) def show_orders(message): if str(message.from_user.id) != ADMIN_ID: return bot.send_message(message.chat.id, "❌ هذا الأمر مخصص للأدمن فقط.") if not os.path.exists("orders.json"): return bot.send_message(message.chat.id, "لا توجد طلبات حالياً.") with open("orders.json", "r") as f: orders = json.load(f) if not orders: return bot.send_message(message.chat.id, "لا توجد طلبات حالياً.") text = "قائمة الطلبات:\n\n" for i, order in enumerate(orders, 1): text += f"{i}. @{order['username']} - {order['link']} - {order['amount']} متابع - {order['cost']} نقطة\n" bot.send_message(message.chat.id, text)

print("البوت يعمل...") bot.infinity_polling()

