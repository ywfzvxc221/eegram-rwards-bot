import os
import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# التوكن و معرف الأدمن
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# قاعدة البيانات
conn = sqlite3.connect("store.db", check_same_thread=False)
cur = conn.cursor()

# إنشاء الجداول
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

cur.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER,
    referrals INTEGER DEFAULT 0
)''')

conn.commit()

# /start
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    user_id = message.from_user.id

    # التحقق إذا كان المستخدم موجود
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    exists = cur.fetchone()

    if not exists:
        referrer_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
        cur.execute("INSERT INTO users (user_id, referrer_id, referrals) VALUES (?, ?, ?)", (user_id, referrer_id, 0))
        if referrer_id:
            cur.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 تصفح المنتجات", "🧾 طلباتي")
    kb.add("💳 طريقة الدفع", "📞 الدعم الفني")
    kb.add("🎁 دعوة الأصدقاء")
    if user_id == ADMIN_ID:
        kb.add("👑 لوحة الإدارة")
    bot.send_message(user_id, "مرحبًا بك في متجرنا الرقمي!", reply_markup=kb)

# دعوة الأصدقاء
@bot.message_handler(func=lambda m: m.text == "🎁 دعوة الأصدقاء")
def invite_friends(message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    # عدد الإحالات
    cur.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    referrals = result[0] if result else 0

    share_text = f"جرب هذا البوت الرائع للتسوق عبر تيليجرام واحصل على هدايا عند التسجيل:\n{referral_link}"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔗 شارك الآن", url=f"https://t.me/share/url?url={referral_link}&text={share_text}"))

    msg = f"""
🎁 *دعوة الأصدقاء*

✅ لقد دعوت حتى الآن: *{referrals}* شخصًا

قم بدعوة أصدقائك باستخدام الرابط الخاص بك واحصل على نقاط وهدايا لكل إحالة ناجحة!

👇 رابطك الخاص:
`{referral_link}`
"""
    bot.send_message(user_id, msg, reply_markup=kb, parse_mode="Markdown")

# (تابع باقي الكود: تصفح المنتجات، الشراء، الدعم، طريقة الدفع، الإدارة...)

# تشغيل البوت
bot.infinity_polling()
