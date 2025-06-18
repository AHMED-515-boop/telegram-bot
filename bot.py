import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# لتحميل ملف .env إذا كان موجود
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على التوكن من متغيرات البيئة أو ضعه هنا مباشرة
BOT_TOKEN = os.environ.get('7750811448:AAHP0G9tkIwNxWyvyO2NH0t5U25Df6_dTrI') or "7750811448:AAHP0G9tkIwNxWyvyO2NH0t5U25Df6_dTrI"

# دالة البداية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f'مرحباً {user.first_name}! 👋\n'
        'أنا بوت بسيط يمكنني:\n'
        '• الرد على الرسائل\n'
        '• إرسال معلومات عنك\n'
        '• المساعدة في أشياء مختلفة\n\n'
        'استخدم /help لرؤية جميع الأوامر'
    )

# دالة المساعدة
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *أوامر البوت:*

/start - بدء المحادثة
/help - عرض هذه المساعدة
/info - معلومات عنك
/echo - تكرار الرسالة
/joke - نكتة عشوائية
/time - الوقت الحالي

📝 يمكنك أيضاً إرسال أي رسالة وسأرد عليها!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# دالة معلومات المستخدم
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    info_text = f"""
👤 *معلوماتك:*

الاسم الأول: {user.first_name}
الاسم الأخير: {user.last_name or 'غير محدد'}
اسم المستخدم: @{user.username or 'غير محدد'}
معرف المستخدم: {user.id}
نوع المحادثة: {chat.type}
    """
    await update.message.reply_text(info_text, parse_mode='Markdown')

# دالة تكرار الرسالة
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = ' '.join(context.args)
    if message:
        await update.message.reply_text(f"🔄 تكرار: {message}")
    else:
        await update.message.reply_text("⚠️ يرجى كتابة رسالة للتكرار\nمثال: /echo السلام عليكم")

# دالة النكت
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = [
        "لماذا لا يمكن للبرمجة أن تكون طبيباً؟\nلأنها دائماً تعطي أخطاء! 😄",
        "ما هو الشيء المشترك بين البرمجة والطبخ؟\nكلاهما يحتاج وصفة جيدة! 👨‍🍳",
        "لماذا يحب المبرمجون القهوة؟\nلأنها تساعدهم على تشغيل الكود! ☕",
        "ما الفرق بين المبرمج والسحر؟\nالساحر يخرج أرنباً من القبعة، والمبرمج يخرج أخطاء من الكود! 🐰",
        "لماذا لا يثق المبرمجون بالدرج؟\nلأنهم دائماً مكسورون! 🪜"
    ]
    
    import random
    joke_text = random.choice(jokes)
    await update.message.reply_text(f"😂 {joke_text}")

# دالة الوقت
async def current_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime
    import pytz
    
    # توقيت القاهرة
    cairo_tz = pytz.timezone('Africa/Cairo')
    now = datetime.now(cairo_tz)
    
    time_text = f"""
🕐 *الوقت الحالي:*

التاريخ: {now.strftime('%Y-%m-%d')}
الوقت: {now.strftime('%H:%M:%S')}
المنطقة الزمنية: القاهرة (GMT+2)
    """
    await update.message.reply_text(time_text, parse_mode='Markdown')

# دالة الرد على الرسائل العادية
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()
    
    responses = {
        'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته 🌸',
        'مرحبا': 'أهلاً وسهلاً بك! 👋',
        'شكرا': 'العفو! سعيد لمساعدتك 😊',
        'كيف حالك': 'بخير والحمد لله! وأنت كيف حالك؟ 😊',
        'ما اسمك': 'أنا بوت مساعد، يمكنك تسميتي كما تشاء! 🤖',
    }
    
    # البحث عن رد مناسب
    response = None
    for key, value in responses.items():
        if key in message:
            response = value
            break
    
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"📝 تلقيت رسالتك: '{update.message.text}'\n"
            "استخدم /help لرؤية الأوامر المتاحة! 🤖"
        )

# دالة معالجة الأخطاء
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info=context.error)

def main():
    if not BOT_TOKEN:
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة")
        return
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", user_info))
    app.add_handler(CommandHandler("echo", echo))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("time", current_time))
    
    # معالج الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأخطاء
    app.add_error_handler(error_handler)
    
    # تشغيل البوت
    print("🚀 البوت يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()