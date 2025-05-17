import os
import json
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# قراءة التوكن ومعرف الأدمن من متغيرات البيئة
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

CATEGORIES_FILE = "categories.json"
PRODUCTS_FILE = "products.json"
IMAGES_DIR = "product_images"

# تأكد من وجود مجلد الصور
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# تحميل الأقسام
def load_categories():
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "w") as f:
            json.dump({}, f)
    with open(CATEGORIES_FILE, "r") as f:
        return json.load(f)

# حفظ الأقسام
def save_categories(categories):
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(categories, f, indent=4, ensure_ascii=False)

# تحميل المنتجات
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

categories = load_categories()
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
def show_categories(message):
    categories = load_categories()
    if not categories:
        bot.send_message(message.chat.id, "🚫 لا توجد أقسام حاليا.")
        return
    kb = InlineKeyboardMarkup(row_width=2)
    for cid, cname in categories.items():
        kb.add(InlineKeyboardButton(cname, callback_data=f"category_{cid}"))
    bot.send_message(message.chat.id, "📂 اختر القسم لتصفح المنتجات:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("category_"))
def show_products_in_category(call):
    cid = call.data.split("_")[1]
    categories = load_categories()
    products = load_products()
    if cid not in categories:
        bot.answer_callback_query(call.id, "القسم غير موجود.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    found = False
    for pid, p in products.items():
        if p.get("category") == cid:
            kb.add(InlineKeyboardButton(f"{p['name']} - {p['price']}", callback_data=f"buy_{pid}"))
            found = True
    if not found:
        bot.edit_message_text("🚫 لا توجد منتجات في هذا القسم.", call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(f"📦 منتجات قسم: {categories[cid]}", call.message.chat.id, call.message.message_id, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def process_buy(call):
    pid = call.data.split("_")[1]
    products = load_products()
    product = products.get(pid)
    if not product:
        bot.answer_callback_query(call.id, "المنتج غير موجود.")
        return
    
    caption = (f"🛒 طلب شراء *{product['name']}*\n"
               f"💵 السعر: {product['price']}\n\n"
               "📧 الرجاء إرسال بريدك الإلكتروني في FaucetPay لإكمال الطلب.")
    
    image_path = product.get("image")
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption=caption, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

    bot.register_next_step_handler(call.message, lambda m: confirm_order(m, product))

def confirm_order(message, product):
    email = message.text.strip()
    bot.send_message(message.chat.id, f"✅ تم استلام طلبك!\n📥 رابط التحميل:\n{product['link']}")
    bot.send_message(ADMIN_ID, f"📬 طلب جديد من @{message.from_user.username or message.from_user.first_name}\n📧 البريد: {email}\n📦 المنتج: {product['name']}")

@bot.message_handler(func=lambda m: m.text == "💰 طريقة الدفع")
def how_to_pay(message):
    text = ("💳 الدفع عبر FaucetPay فقط.\n"
            "ارسل بريدك الإلكتروني المرتبط بـ FaucetPay عند شراء المنتج.\n"
            "بعد الدفع سيتم إرسال رابط التحميل تلقائيًا ✅")
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📞 دعم العملاء")
def support(message):
    bot.send_message(message.chat.id, "📩 للتواصل معنا: @qqw123187")

@bot.message_handler(func=lambda m: m.text == "📥 طلباتي")
def my_orders(message):
    bot.send_message(message.chat.id, "📝 لا توجد طلبات بعد. اشتري منتج لتبدأ.")

# ----- لوحة الإدارة -----

@bot.message_handler(func=lambda m: m.text == "👑 لوحة الإدارة" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("/add_category", "/delete_category")
    kb.add("/add_product", "/delete_product")
    kb.add("/show_categories")
    bot.send_message(message.chat.id,
                     "👑 لوحة الإدارة:\n\n"
                     "- /add_category لإضافة قسم جديد\n"
                     "- /delete_category لحذف قسم\n"
                     "- /add_product لإضافة منتج\n"
                     "- /delete_product لحذف منتج\n"
                     "- /show_categories لعرض الأقسام الحالية",
                     reply_markup=kb)

# إضافة قسم جديد
@bot.message_handler(commands=['add_category'])
def add_category_step1(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "🆕 أدخل اسم القسم الجديد:")
    bot.register_next_step_handler(message, save_category)

def save_category(message):
    cname = message.text.strip()
    categories = load_categories()
    new_id = str(max([int(i) for i in categories.keys()] + [0]) + 1)
    categories[new_id] = cname
    save_categories(categories)
    bot.send_message(message.chat.id, f"✅ تم إضافة القسم: *{cname}*", parse_mode="Markdown")

# حذف قسم
@bot.message_handler(commands=['delete_category'])
def delete_category_step1(message):
    if message.from_user.id != ADMIN_ID:
        return
    categories = load_categories()
    if not categories:
        bot.send_message(message.chat.id, "🚫 لا توجد أقسام لحذفها.")
        return
    kb = InlineKeyboardMarkup(row_width=2)
    for cid, cname in categories.items():
        kb.add(InlineKeyboardButton(cname, callback_data=f"delcat_{cid}"))
    bot.send_message(message.chat.id, "🗑️ اختر القسم الذي تريد حذفه:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("delcat_"))
def delete_category(call):
    cid = call.data.split("_")[1]
    categories = load_categories()
    products = load_products()
    if cid not in categories:
        bot.answer_callback_query(call.id, "القسم غير موجود.")
        return
    # حذف المنتجات المرتبطة بالقسم
    products = {pid: p for pid, p in products.items() if p.get("category") != cid}
    save_products(products)
    # حذف القسم
    cname = categories.pop(cid)
    save_categories(categories)
    bot.edit_message_text(f"✅ تم حذف القسم: {cname} وجميع المنتجات المرتبطة به.", call.message.chat.id, call.message.message_id)

# إضافة منتج مع وصف وصورة
@bot.message_handler(commands=['add_product'])
def add_product_step1(message):
    if message.from_user.id != ADMIN_ID:
        return
    categories = load_categories()
    if not categories:
        bot.send_message(message.chat.id, "🚫 لا توجد أقسام! الرجاء إضافة قسم أولاً باستخدام /add_category")
        return
    kb = InlineKeyboardMarkup(row_width=2)
    for cid, cname in categories.items():
        kb.add(InlineKeyboardButton(cname, callback_data=f"select_cat_{cid}"))
    bot.send_message(message.chat.id, "📂 اختر القسم الذي سينتمي إليه المنتج:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("select_cat_"))
def select_category(call):
    cid = call.data.split("_")[-1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "📝 أدخل اسم المنتج:")
    bot.register_next_step_handler(call.message, get_name, cid)

def get_name(message, cid):
    name = message.text.strip()
    bot.send_message(message.chat.id, "🖊️
