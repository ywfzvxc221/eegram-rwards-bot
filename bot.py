import telebot
from telebot import types
import time
import json
import os

# إعدادات من ملف البيئة أو مباشرة
BOT_TOKEN = os.getenv("BOT_TOKEN", "توكن_البوت")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
FAUCET_EMAIL = os.getenv("FAUCET_EMAIL", "you@example.com")
PROOF_CHANNEL = os.getenv("PROOF_CHANNEL", "@proofchannel")
REWARD_DAILY = int(os.getenv("REWARD_DAILY", "20"))
REWARD_AD = int(os.getenv("REWARD_AD", "15"))
MIN_WITHDRAW = int(os.getenv("MIN_WITHDRAW", "1000"))
WITHDRAW_METHODS = ["FaucetPay", "Binance"]

bot = telebot.TeleBot(BOT_TOKEN)
DATA_FILE = "users.json"

# تحميل البيانات أو إنشاؤها
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

users = load_data()

# أدوات مساعدة
def get_user(uid):
    if str(uid) not in users:
        users[str(uid)] = {
            "balance": 0,
            "referrals": 0,
            "total_earned": 0,
            "last_daily": 0,
            "ref_by": None,
            "wallet": {"faucet": "", "binance": ""},
        }
    return users[str(uid)]

def referral_link(uid):
    return f"https://t.me/{bot.get_me().username}?start={uid}"

# بدء البوت
@bot.message_handler(commands=["start"])
def start_handler(message):
    uid = message.from_user.id
    args = message.text.split()
    user = get_user(uid)

    if len(args) == 2:
        ref_id = args[1]
        if user["ref_by"] is None and ref_id != str(uid):
            user["ref_by"] = ref_id
            ref_user = get_user(ref_id)
            ref_user["referrals"] += 1
            save_data(users)

    bot.send_message(
        uid,
        f"مرحبًا بك في بوت ربح البيتكوين!\n\n"
        "استخدم الأزرار بالأسفل للتنقل.",
        reply_markup=main_keyboard(),
    )
    save_data(users)

# لوحة المفاتيح الرئيسية
def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 حسابي", "🎁 المكافأة اليومية")
    kb.row("👥 دعوة الأصدقاء", "🎯 المهام اليومية")
    kb.row("💸 سحب الأرباح", "📞 الدعم الفني")
    kb.row("📺 شاهد إعلان")
    return kb

# زر: حسابي
@bot.message_handler(func=lambda m: m.text == "📊 حسابي")
def my_account(message):
    uid = message.from_user.id
    user = get_user(uid)
    bot.send_message(
        uid,
        f"رصيدك الحالي: {user['balance']} ساتوشي\n"
        f"عدد الإحالات: {user['referrals']}\n"
        f"إجمالي الأرباح: {user['total_earned']} ساتوشي\n"
        f"رابط الدعوة: {referral_link(uid)}"
    )

# زر: المكافأة اليومية
@bot.message_handler(func=lambda m: m.text == "🎁 المكافأة اليومية")
def daily_reward(message):
    uid = message.from_user.id
    user = get_user(uid)
    now = time.time()
    if now - user["last_daily"] >= 86400:
        user["balance"] += REWARD_DAILY
        user["total_earned"] += REWARD_DAILY
        user["last_daily"] = now
        save_data(users)
        bot.send_message(uid, f"تم إضافة {REWARD_DAILY} ساتوشي إلى رصيدك!")
    else:
        remaining = int(86400 - (now - user["last_daily"]))
        h, m, s = remaining // 3600, (remaining % 3600) // 60, remaining % 60
        bot.send_message(uid, f"الرجاء الانتظار {h} ساعة و {m} دقيقة قبل المطالبة مرة أخرى.")

# زر: دعوة الأصدقاء
@bot.message_handler(func=lambda m: m.text == "👥 دعوة الأصدقاء")
def invite(message):
    uid = message.from_user.id
    link = referral_link(uid)
    bot.send_message(uid, f"شارك هذا الرابط لدعوة أصدقائك:\n{link}")

# زر: الدعم الفني
@bot.message_handler(func=lambda m: m.text == "📞 الدعم الفني")
def support(message):
    bot.send_message(message.chat.id, f"للتواصل مع الدعم: @{bot.get_me().username}")

# زر: سحب الأرباح
@bot.message_handler(func=lambda m: m.text == "💸 سحب الأرباح")
def withdraw(message):
    uid = message.from_user.id
    user = get_user(uid)

    if user["balance"] < MIN_WITHDRAW:
        bot.send_message(uid, f"الحد الأدنى للسحب هو {MIN_WITHDRAW} ساتوشي.")
        return

    markup = types.InlineKeyboardMarkup()
    for method in WITHDRAW_METHODS:
        markup.add(types.InlineKeyboardButton(method, callback_data=f"withdraw_{method.lower()}"))
    bot.send_message(uid, "اختر طريقة السحب:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("withdraw_"))
def handle_withdraw_method(call):
    method = call.data.split("_")[1]
    uid = call.from_user.id
    user = get_user(uid)

    if method == "faucetpay":
        msg = bot.send_message(uid, "أدخل بريد FaucetPay:")
        bot.register_next_step_handler(msg, lambda m: process_withdraw(m, "faucetpay"))
    elif method == "binance":
        msg = bot.send_message(uid, "أدخل عنوان محفظتك على شبكة Bitcoin:")
        bot.register_next_step_handler(msg, lambda m: process_withdraw(m, "binance"))

def process_withdraw(message, method):
    uid = message.from_user.id
    user = get_user(uid)
    address = message.text.strip()

    if method == "faucetpay":
        user["wallet"]["faucet"] = address
    else:
        user["wallet"]["binance"] = address

    amount = user["balance"]
    user["balance"] = 0
    save_data(users)

    text = (
        f"طلب سحب جديد:\n"
        f"المستخدم: {uid}\n"
        f"الطريقة: {method}\n"
        f"المبلغ: {amount} ساتوشي\n"
        f"العنوان: {address}"
    )

    bot.send_message(uid, "تم إرسال طلب السحب! سيتم المعالجة خلال 24 ساعة.")
    bot.send_message(PROOF_CHANNEL, text)

# زر: شاهد إعلان (placeholder)
@bot.message_handler(func=lambda m: m.text == "📺 شاهد إعلان")
def watch_ad(message):
    bot.send_message(message.chat.id, "لا توجد إعلانات متاحة حاليًا.")

# زر: المهام اليومية (placeholder)
@bot.message_handler(func=lambda m: m.text == "🎯 المهام اليومية")
def tasks(message):
    bot.send_message(message.chat.id, "سيتم إضافة المهام قريبًا!")

# بدء البوت
print("Bot is running...")
# ====== لوحة تحكم الأدمن ======

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ إضافة مهمة جديدة", "📋 عرض كل المهام")
    markup.add("⬅️ رجوع")
    bot.send_message(message.chat.id, "مرحبًا بك في لوحة التحكم، اختر إجراء:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "➕ إضافة مهمة جديدة" and str(message.from_user.id) == ADMIN_ID)
def add_new_task(message):
    bot.send_message(message.chat.id, "أرسل عنوان المهمة (مثلاً: اشترك في قناة @xyz)")
    bot.register_next_step_handler(message, save_task_title)

def save_task_title(message):
    task_title = message.text
    bot.send_message(message.chat.id, "أرسل الرابط (مثلاً: https://t.me/xyz)")
    bot.register_next_step_handler(message, lambda msg: save_task_link(msg, task_title))

def save_task_link(message, task_title):
    task_link = message.text
    new_task = {"title": task_title, "link": task_link}
    
    try:
        with open("ads.json", "r", encoding="utf-8") as f:
            ads = json.load(f)
    except:
        ads = []

    ads.append(new_task)
    
    with open("ads.json", "w", encoding="utf-8") as f:
        json.dump(ads, f, ensure_ascii=False, indent=4)
    
    bot.send_message(message.chat.id, "تمت إضافة المهمة بنجاح!")

@bot.message_handler(func=lambda message: message.text == "📋 عرض كل المهام" and str(message.from_user.id) == ADMIN_ID)
def list_tasks(message):
    try:
        with open("ads.json", "r", encoding="utf-8") as f:
            ads = json.load(f)
    except:
        ads = []

    if not ads:
        bot.send_message(message.chat.id, "لا توجد مهام حالياً.")
        return

    msg = "قائمة المهام الحالية:\n\n"
    for i, ad in enumerate(ads, start=1):
        msg += f"{i}. {ad['title']}\n{ad['link']}\n\n"

    bot.send_message(message.chat.id, msg)

# ====== مشاركة رابط الإحالة برسالة ترويجية ======

@bot.message_handler(func=lambda message: message.text == "👥 دعوة الأصدقاء")
def referral_menu(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data(user_id)
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    msg = f"""👥 *دعوة الأصدقاء*
شارك رابطك لربح 5% من أرباح كل شخص يسجل عن طريقك!

رابطك الشخصي:
{referral_link}
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔗 مشاركة على واتساب", url=f"https://wa.me/?text=ربح%20بيتكوين%20مجانا!%20سجل%20من%20هنا:%20{referral_link}"))
    markup.add(types.InlineKeyboardButton("📢 مشاركة على تيليجرام", url=f"https://t.me/share/url?url={referral_link}&text=احصل%20على%20بيتكوين%20مجاناً%20من%20هذا%20البوت!"))
    markup.add(types.InlineKeyboardButton("🌍 مشاركة على تويتر", url=f"https://twitter.com/intent/tweet?text=احصل%20على%20بيتكوين%20مجاناً%20من%20هذا%20البوت!%20{referral_link}"))

    bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=markup)
bot.infinity_polling()
