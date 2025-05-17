import os
import json
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# قراءة التوكن ومعرف الأدمن من متغيرات البيئة
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

PRODUCTS_FILE = "products.json"

# تحميل المنتجات من الملف
def load_products():
    if not os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "w") as f:
            json.dump({}, f)
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)

# حفظ المنتجات
def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4, ensure_ascii=False)

products = load_products()

@bot.message_handler(commands=['start'])
def start(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛍️ تصفح المنتجات", "📥 طلباتي")
    kb.add("💰 طريقة الدفع", "📞 دعم العملاء")
    if message.from_user.id == ADMIN_ID:
        kb.add("👑 لوحة الإدارة")
    bot.send_message(message.chat.id, f"مرحبًا بك في متجر المنتجات الرقمية 🎉", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "🛍️ تصفح المنتجات")
def show_products(message):
    products = load_products()
    if not products:
        bot.send_message(message.chat.id, "🚫 لا توجد منتجات حالياً.")
        return
    for pid, p in products.items():
        btn = InlineKeyboardMarkup()
        btn.add(InlineKeyboardButton("🛒 شراء", callback_data=f"buy_{pid}"))
        msg = f"📦 *{p['name']}*\n\n{p['desc']}\n\n💰 السعر: {p['price']}"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=btn)

@bot.message_handler(func=lambda m: m.text == "💰 طريقة الدفع")
def how_to_pay(message):
    text = ("💳 الدفع عبر FaucetPay فقط.\n"
            "ارسل بريدك الإلكتروني المرتبط بـ FaucetPay عند شراء المنتج.\n"
            "بعد الدفع سيتم إرسال رابط التحميل تلقائيًا ✅")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📞 دعم العملاء")
def support(message):
    bot.send_message(message.chat.id, "📩 للتواصل معنا: @qqw123187")

@bot.message_handler(func=lambda m: m.text == "👑 لوحة الإدارة" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    bot.send_message(message.chat.id, "👑 لوحة الإدارة:\n\nأرسل الأمر /add_product لإضافة منتج جديد.")

@bot.message_handler(func=lambda m: m.text == "📥 طلباتي")
def my_orders(message):
    bot.send_message(message.chat.id, "📝 لا توجد طلبات بعد. اشتري منتج لتبدأ.")

@bot.message_handler(commands=['add_product'])
def add_product_step1(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "📝 أدخل *اسم المنتج*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text.strip()
    bot.send_message(message.chat.id, "🖊️ أدخل *وصف المنتج*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, get_desc, name)

def get_desc(message, name):
    desc = message.text.strip()
    bot.send_message(message.chat.id, "💰 أدخل *سعر المنتج* (مثال: 1 TON):", parse_mode="Markdown")
    bot.register_next_step_handler(message, get_price, name, desc)

def get_price(message, name, desc):
    price = message.text.strip()
    bot.send_message(message.chat.id, "🔗 أدخل *رابط التحميل*:", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_product, name, desc, price)

def save_product(message, name, desc, price):
    link = message.text.strip()
    products = load_products()
    new_id = max([int(i) for i in products.keys()] + [0]) + 1
    products[new_id] = {
        "name": name,
        "desc": desc,
        "price": price,
        "link": link
    }
    save_products(products)
    bot.send_message(message.chat.id, f"✅ تم إضافة المنتج *{name}* بنجاح!", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def process_buy(call):
    pid = c.data.split("_")[1]
    products = load_products()
    product = products.get(pid)
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود.")
        return
    msg = (f"🛒 طلب شراء *{product['name']}*\n"
           f"💵 السعر: {product['price']}\n\n"
           "📧 الرجاء إرسال بريدك الإلكتروني في FaucetPay لإكمال الطلب.")
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")
    bot.register_next_step_handler(call.message, lambda m: confirm_order(m, product))

def confirm_order(message, product):
    email = message.text.strip()
    bot.send_message(message.chat.id, f"✅ تم استلام طلبك!\n📥 رابط التحميل:\n{product['link']}")
    bot.send_message(ADMIN_ID, f"📬 طلب جديد من @{message.from_user.username or message.from_user.first_name}\n📧 البريد: {email}\n📦 المنتج: {product['name']}")

bot.infinity_polling()
