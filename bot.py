import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# قراءة التوكن ومعرف الأدمن من متغيرات البيئة
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# المنتجات
products = {
    1: {
        "name": "دورة تصميم منتجات رقمية",
        "desc": "دورة بصيغة PDF وڤيديوهات لتعلم إنشاء منتجات رقمية.",
        "price": "1 TON",
        "link": "https://example.com/product1"
    }
}

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
    bot.send_message(message.chat.id, "👑 لوحة الإدارة:\nحاليًا لا يمكن إضافة منتجات من البوت (تتم من الكود).")

@bot.message_handler(func=lambda m: m.text == "📥 طلباتي")
def my_orders(message):
    bot.send_message(message.chat.id, "📝 لا توجد طلبات بعد. اشتري منتج لتبدأ.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def process_buy(call):
    pid = int(call.data.split("_")[1])
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
