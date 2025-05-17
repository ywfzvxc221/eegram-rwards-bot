import telebot
import os
from telebot import types

# ✅ جلب التوكن ومعرف الأدمن من متغيرات البيئة
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN)

# ✅ قاعدة بيانات بسيطة (مؤقتة في الذاكرة فقط)
users = set()

# ✅ لوحة المستخدم
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton("👥 الربح من دعوة الأصدقاء"),
        types.KeyboardButton("🧾 حسابي")
    )
    keyboard.add(
        types.KeyboardButton("📮 الهدية"),
        types.KeyboardButton("💳 سحب الأرباح")
    )
    keyboard.add(
        types.KeyboardButton("📞 الدعم الفني"),
        types.KeyboardButton("🎁 شاهد إعلان")
    )
    return keyboard

# ✅ لوحة تحكم الأدمن
def admin_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton("👥 عدد المستخدمين"),
        types.KeyboardButton("📤 إرسال جماعي")
    )
    keyboard.add(
        types.KeyboardButton("📊 الإحصائيات"),
        types.KeyboardButton("🔄 تحديث البوت")
    )
    keyboard.add(
        types.KeyboardButton("🚫 حظر مستخدم"),
        types.KeyboardButton("🔙 رجوع")
    )
    return keyboard

# ✅ بدء البوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    users.add(message.chat.id)  # تسجيل المستخدم
    name = message.from_user.first_name
    reply = f"👋 مرحباً {name}!\nأهلاً بك في بوت الربح من الريال القطري.\nاختر من القائمة أدناه:"
    bot.send_message(message.chat.id, reply, reply_markup=main_menu())

# ✅ لوحة تحكم الأدمن
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👑 مرحباً بك في لوحة التحكم", reply_markup=admin_menu())
    else:
        bot.send_message(message.chat.id, "🚫 هذا القسم مخصص للإدارة فقط.")

# ✅ التعامل مع الأزرار
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    text = message.text

    # 🟩 أوامر الأدمن
    if user_id == ADMIN_ID:
        if text == "👥 عدد المستخدمين":
            bot.send_message(message.chat.id, f"📊 عدد المستخدمين: {len(users)}")
        elif text == "📤 إرسال جماعي":
            bot.send_message(message.chat.id, "✉️ أرسل الآن الرسالة التي تريد إرسالها لكل الأعضاء.")
            bot.register_next_step_handler(message, broadcast_message)
        elif text == "📊 الإحصائيات":
            bot.send_message(message.chat.id, f"📈 المستخدمين: {len(users)}\n📌 الإعلانات: 0 (مثال)")
        elif text == "🔄 تحديث البوت":
            bot.send_message(message.chat.id, "🔁 تم تحديث إعدادات البوت بنجاح.")
        elif text == "🚫 حظر مستخدم":
            bot.send_message(message.chat.id, "✋ أرسل معرف المستخدم لحظره (غير مفعّل فعليًا هنا).")
        elif text == "🔙 رجوع":
            bot.send_message(message.chat.id, "↩️ العودة إلى القائمة:", reply_markup=main_menu())
            return

    # 🟦 أوامر المستخدم
    if text == "🧾 حسابي":
        bot.send_message(message.chat.id, "📊 حسابك قيد المعالجة...")
    elif text == "👥 الربح من دعوة الأصدقاء":
        bot.send_message(message.chat.id, "🎁 شارك رابط الإحالة مع أصدقائك!")
    elif text == "📮 الهدية":
        bot.send_message(message.chat.id, "🎉 تم إرسال هديتك اليومية!")
    elif text == "💳 سحب الأرباح":
        bot.send_message(message.chat.id, "💰 يرجى إدخال وسيلة السحب.")
    elif text == "📞 الدعم الفني":
        bot.send_message(message.chat.id, "📞 للتواصل مع الدعم، راسل الأدمن.")
    elif text == "🎁 شاهد إعلان":
        bot.send_message(message.chat.id, "🎬 جارٍ تحميل الإعلان...")
    else:
        bot.send_message(message.chat.id, "❓ لم أفهم طلبك. الرجاء اختيار زر من القائمة.")

# ✅ إرسال جماعي
def broadcast_message(message):
    text = message.text
    count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, text)
            count += 1
        except:
            continue
    bot.send_message(message.chat.id, f"✅ تم إرسال الرسالة إلى {count} مستخدم.")

# ✅ تشغيل البوت
bot.polling(none_stop=True)
