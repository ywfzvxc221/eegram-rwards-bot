import telebot
import json
import os
from datetime import datetime, timedelta

# قراءة التوكن من متغيرات البيئة
TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

DATA_FILE = "users.json"
REFERRAL_BONUS = 2
DAILY_BONUS = 1
MINIMUM_WITHDRAWAL = 100

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_user(user_id):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "points": 0,
            "referrals": [],
            "joined": str(datetime.now()),
            "last_bonus": "",
            "earnings": 0
        }
        save_users(users)
    return users[user_id]

def update_user(user_id, user_data):
    users = load_users()
    users[str(user_id)] = user_data
    save_users(users)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_id = message.chat.id
    users = load_users()
    user_id_str = str(user_id)

    if user_id_str not in users:
        ref_id = message.text.split("/start ")
        if len(ref_id) > 1 and ref_id[1] != user_id_str:
            referrer_id = ref_id[1]
            ref_user = get_user(referrer_id)
            ref_user["points"] += REFERRAL_BONUS
            ref_user["referrals"].append(user_id_str)
            update_user(referrer_id, ref_user)

    get_user(user_id)  # Ensure user is created

    welcome_msg = (
        f"مرحبًا بك في بوت الربح من الإنترنت!\n\n"
        f"قم بإكمال المهام اليومية، ودعوة أصدقائك، واجمع النقاط لتستبدلها بأرباح حقيقية!\n\n"
        f"اضغط على الأزرار في الأسفل للبدء."
    )

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎁 المكافأة اليومية", "👥 دعوة الأصدقاء")
    markup.row("📊 إحصائياتي", "📋 المهام اليومية")
    markup.row("💸 سحب الأرباح", "📢 عرض الإعلانات")
    bot.send_message(user_id, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🎁 المكافأة اليومية")
def daily_bonus(message):
    user_id = message.chat.id
    user_data = get_user(user_id)
    now = datetime.now()

    if user_data.get("last_bonus"):
        last_bonus_time = datetime.strptime(user_data["last_bonus"], "%Y-%m-%d")
        if now.date() == last_bonus_time.date():
            bot.send_message(user_id, "لقد حصلت على مكافأتك اليومية اليوم بالفعل. عد غدًا!")
            return

    user_data["points"] += DAILY_BONUS
    user_data["earnings"] += DAILY_BONUS
    user_data["last_bonus"] = str(now.date())
    update_user(user_id, user_data)

    bot.send_message(user_id, f"تم إضافة {DAILY_BONUS} نقاط إلى رصيدك! استخدمها للحصول على مزايا أو سحب الأرباح.")

@bot.message_handler(func=lambda message: message.text == "📊 إحصائياتي")
def my_stats(message):
    user_id = message.chat.id
    user_data = get_user(user_id)

    msg = (
        f"📊 *إحصائياتك:*\n"
        f"- الرصيد: *{user_data['points']} نقاط*\n"
        f"- الأرباح: *{user_data['earnings']} نقاط*\n"
        f"- عدد الإحالات: *{len(user_data['referrals'])} إحالة*\n"
        f"- تاريخ الانضمام: *{user_data['joined'].split()[0]}*"
    )
    bot.send_message(user_id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👥 دعوة الأصدقاء")
def invite_friends(message):
    user_id = message.chat.id
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    msg = (
        f"*دعوة الأصدقاء - اربح النقاط بسهولة!*\n\n"
        f"شارك رابط الإحالة الخاص بك مع أصدقائك واربح *{REFERRAL_BONUS} نقاط* عن كل إحالة ناجحة!\n\n"
        f"*رابط الإحالة الخاص بك:*\n{referral_link}\n\n"
        f"كلما زاد عدد الأشخاص الذين ينضمون عبر رابطك، زادت أرباحك!\n\n"
        f"✅ لا تنسَ مشاركته على وسائل التواصل الاجتماعي لزيادة فرص الربح."
    )
    bot.send_message(user_id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💸 سحب الأرباح")
def withdraw_earnings(message):
    user_id = message.chat.id
    user_data = get_user(user_id)
    earnings = user_data.get("earnings", 0)

    msg = (
        f"*💸 سحب الأرباح*\n\n"
        f"رصيدك الحالي هو: *{earnings} نقاط*\n\n"
        f"للسحب، يجب أن يكون لديك على الأقل *{MINIMUM_WITHDRAWAL} نقاط*.\n"
        f"يرجى التواصل مع الأدمن لإتمام عملية السحب."
    )
    bot.send_message(user_id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📋 المهام اليومية")
def daily_tasks(message):
    user_id = message.chat.id

    tasks_msg = (
        "*📋 المهام اليومية:*\n\n"
        "1. مشاهدة الإعلانات (🔁 كل إعلان = 0.5 نقطة)\n"
        "2. دعوة الأصدقاء (كل إحالة = 2 نقطة)\n"
        "3. الاشتراك في القنوات (1 نقطة لكل قناة)\n"
        "4. المكافأة اليومية (🎁 كل 24 ساعة)\n\n"
        "أكمل المهام اليومية لزيادة رصيدك!"
    )
    bot.send_message(user_id, tasks_msg, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📢 عرض الإعلانات")
def show_ads(message):
    bot.send_message(message.chat.id, "🚧 لا توجد إعلانات حاليًا، تابعنا ليصلك كل جديد.")

bot.infinity_polling()
