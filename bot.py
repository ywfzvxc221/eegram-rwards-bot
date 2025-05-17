import telebot
import json
import os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# التأكد من وجود ملف الطلبات
ORDERS_FILE = "orders.json"
if not os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "w") as f:
        json.dump([], f)

# إرسال قائمة الطلبات للأدمن
@bot.message_handler(commands=['الطلبات'])
def view_orders(message):
    if message.from_user.id != ADMIN_ID:
        return
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
    if not orders:
        bot.send_message(message.chat.id, "لا توجد طلبات حالياً.")
        return
    text = "قائمة الطلبات:\n\n"
    for idx, order in enumerate(orders, start=1):
        text += f"{idx}. المستخدم: {order['user_id']}\nالقسم: {order['section']}\nالرابط: {order['link']}\nالكمية: {order['quantity']}\nالتاريخ: {order['timestamp']}\n\n"
    bot.send_message(message.chat.id, text)

# تقديم الطلب من المستخدم
@bot.message_handler(commands=['طلب'])
def make_order(message):
    msg = bot.send_message(message.chat.id, "أدخل القسم (مثال: متابعين، لايكات):")
    bot.register_next_step_handler(msg, process_section)

def process_section(message):
    section = message.text
    msg = bot.send_message(message.chat.id, "أدخل رابط الحساب أو المنشور:")
    bot.register_next_step_handler(msg, process_link, section)

def process_link(message, section):
    link = message.text
    msg = bot.send_message(message.chat.id, "أدخل الكمية المطلوبة:")
    bot.register_next_step_handler(msg, process_quantity, section, link)

def process_quantity(message, section, link):
    try:
        quantity = int(message.text)
    except:
        bot.send_message(message.chat.id, "الرجاء إدخال رقم صحيح.")
        return
    order = {
        "user_id": message.from_user.id,
        "section": section,
        "link": link,
        "quantity": quantity,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
    orders.append(order)
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    bot.send_message(message.chat.id, "تم استلام طلبك بنجاح، سيتم مراجعته قريباً.")

# بدء التشغيل
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحباً بك! لإرسال طلب رشق، استخدم الأمر /طلب.\nلعرض الطلبات (للأدمن فقط): /الطلبات")

print("البوت يعمل...")
bot.polling()
