import os
import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# قراءة التوكن ومعرف الأدمن من متغيرات البيئة
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# إنشاء قاعدة البيانات
conn = sqlite3.connect("store.db", check_same_thread=False)
cur = conn.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)''')

cur.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price TEXT,
    category_id INTEGER,
    link TEXT
)''')

cur.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    email TEXT
)''')

conn.commit()

# /start
@bot.message_handler(commands=['start'])
def start(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 تصفح المنتجات", "🧾 طلباتي")
    kb.add("💳 طريقة الدفع", "📞 الدعم الفني")
    if message.from_user.id == ADMIN_ID:
        kb.add("👑 لوحة الإدارة")
    bot.send_message(message.chat.id, "مرحبًا بك في متجرنا الرقمي!", reply_markup=kb)

# عرض الأقسام
@bot.message_handler(func=lambda m: m.text == "🛒 تصفح المنتجات")
def browse(message):
    cur.execute("SELECT * FROM categories")
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "🚫 لا توجد أقسام متاحة.")
        return
    kb = InlineKeyboardMarkup(row_width=2)
    for row in rows:
        kb.add(InlineKeyboardButton(f"📂 {row[1]}", callback_data=f"cat_{row[0]}"))
    bot.send_message(message.chat.id, "اختر القسم:", reply_markup=kb)

# عرض المنتجات في القسم
@bot.callback_query_handler(func=lambda call: call.data.startswith("cat_"))
def show_products(call):
    cid = int(call.data.split("_")[1])
    cur.execute("SELECT * FROM products WHERE category_id=?", (cid,))
    rows = cur.fetchall()
    if not rows:
        bot.answer_callback_query(call.id, "لا توجد منتجات في هذا القسم.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for row in rows:
        kb.add(InlineKeyboardButton(f"{row[1]} - 💵 {row[2]}", callback_data=f"buy_{row[0]}"))
    bot.edit_message_text("📦 اختر منتجًا:", call.message.chat.id, call.message.message_id, reply_markup=kb)

# تأكيد الشراء
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy_product(call):
    pid = int(call.data.split("_")[1])
    cur.execute("SELECT name, price FROM products WHERE id=?", (pid,))
    product = cur.fetchone()
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود.")
        return
    msg = f"🛒 المنتج: {product[0]}\n💰 السعر: {product[1]}\n\nأرسل بريدك الإلكتروني على FaucetPay لإتمام الطلب."
    bot.send_message(call.message.chat.id, msg)
    bot.register_next_step_handler(call.message, lambda m: confirm_order(m, pid))

def confirm_order(message, pid):
    email = message.text.strip()
    cur.execute("INSERT INTO orders (user_id, product_id, email) VALUES (?, ?, ?)",
                (message.from_user.id, pid, email))
    conn.commit()

    cur.execute("SELECT name, link FROM products WHERE id=?", (pid,))
    product = cur.fetchone()

    bot.send_message(message.chat.id, f"✅ تم الشراء بنجاح!\nرابط التحميل:\n{product[1]}")
    bot.send_message(ADMIN_ID, f"طلب جديد من @{message.from_user.username or message.from_user.first_name}:\nمنتج: {product[0]}\n📧 الإيميل: {email}")

# طريقة الدفع
@bot.message_handler(func=lambda m: m.text == "💳 طريقة الدفع")
def payment(message):
    bot.send_message(message.chat.id, "💳 الدفع يتم عبر FaucetPay فقط.\nأرسل بريدك الإلكتروني عند الشراء.")

# الدعم
@bot.message_handler(func=lambda m: m.text == "📞 الدعم الفني")
def support(message):
    bot.send_message(message.chat.id, "📞 تواصل معنا عبر: @YourSupportBot")

# طلباتي
@bot.message_handler(func=lambda m: m.text == "🧾 طلباتي")
def my_orders(message):
    cur.execute("SELECT p.name, o.email FROM orders o JOIN products p ON o.product_id = p.id WHERE o.user_id=?", (message.from_user.id,))
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "🚫 لا توجد طلبات مسجلة.")
        return
    txt = "📦 طلباتك:\n\n"
    for i, row in enumerate(rows, 1):
        txt += f"{i}. {row[0]} | {row[1]}\n"
    bot.send_message(message.chat.id, txt)

# لوحة الإدارة
@bot.message_handler(func=lambda m: m.text == "👑 لوحة الإدارة" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("/add_category", "/add_product", "/view_orders")
    bot.send_message(message.chat.id, "👑 لوحة الإدارة:", reply_markup=kb)

# إضافة قسم
@bot.message_handler(commands=['add_category'])
def add_category(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "📂 أرسل اسم القسم:")
    bot.register_next_step_handler(message, save_category)

def save_category(message):
    name = message.text.strip()
    cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ تم إضافة القسم: {name}")

# إضافة منتج
@bot.message_handler(commands=['add_product'])
def add_product(message):
    if message.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT * FROM categories")
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "❌ لا توجد أقسام. أضف قسمًا أولًا.")
        return
    kb = InlineKeyboardMarkup()
    for row in rows:
        kb.add(InlineKeyboardButton(row[1], callback_data=f"addprod_{row[0]}"))
    bot.send_message(message.chat.id, "اختر القسم:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("addprod_"))
def add_product_details(call):
    cat_id = int(call.data.split("_")[1])
    bot.send_message(call.message.chat.id, "📝 أرسل اسم المنتج:")
    bot.register_next_step_handler(call.message, lambda m: get_price(m, cat_id))

def get_price(message, cat_id):
    name = message.text.strip()
    bot.send_message(message.chat.id, "💵 أرسل السعر:")
    bot.register_next_step_handler(message, lambda m: get_link(m, name, cat_id))

def get_link(message, name, cat_id):
    price = message.text.strip()
    bot.send_message(message.chat.id, "🔗 أرسل رابط التحميل:")
    bot.register_next_step_handler(message, lambda m: save_product(m, name, price, cat_id))

def save_product(message, name, price, cat_id):
    link = message.text.strip()
    cur.execute("INSERT INTO products (name, price, category_id, link) VALUES (?, ?, ?, ?)",
                (name, price, cat_id, link))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ تم إضافة المنتج: {name}")

# عرض الطلبات
@bot.message_handler(commands=['view_orders'])
def view_orders(message):
    if message.from_user.id != ADMIN_ID:
        return
    cur.execute("SELECT o.id, p.name, o.email FROM orders o JOIN products p ON o.product_id = p.id")
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "❌ لا توجد طلبات.")
        return
    txt = "📬 الطلبات:\n\n"
    for row in rows:
        txt += f"#{row[0]} - {row[1]} | {row[2]}\n"
    bot.send_message(message.chat.id, txt)

# تشغيل البوت
bot.infinity_polling()
