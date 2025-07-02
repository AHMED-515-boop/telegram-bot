import os
import logging
import json
import signal
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# إعداد السجلات للإنتاج

logging.basicConfig(
format=’%(asctime)s - %(name)s - %(levelname)s - %(message)s’,
level=logging.WARNING,  # تقليل مستوى السجلات للإنتاج
handlers=[
logging.StreamHandler(sys.stdout)
]
)
logger = logging.getLogger(**name**)

# إعدادات البوت من متغيرات البيئة

BOT_TOKEN = os.environ.get(‘BOT_TOKEN’)
ADMIN_ID = os.environ.get(‘ADMIN_ID’)

# التحقق من وجود المتغيرات المطلوبة

if not BOT_TOKEN:
logger.error(“BOT_TOKEN environment variable is not set”)
sys.exit(1)

if not ADMIN_ID:
logger.error(“ADMIN_ID environment variable is not set”)
sys.exit(1)

try:
ADMIN_ID = int(ADMIN_ID)
except ValueError:
logger.error(“ADMIN_ID must be a valid integer”)
sys.exit(1)

# قاموس لحفظ الأسئلة المعلقة (في الذاكرة)

pending_questions = {}
question_counter = 1

# دالة لتحديث عداد الأسئلة

def update_question_counter():
global question_counter
try:
if pending_questions:
existing_numbers = []
for q_id in pending_questions.keys():
if q_id.startswith(‘Q’) and q_id[1:].isdigit():
existing_numbers.append(int(q_id[1:]))

```
        if existing_numbers:
            question_counter = max(existing_numbers) + 1
        else:
            question_counter = 1
    else:
        question_counter = 1
except Exception as e:
    logger.error(f"Error updating question counter: {e}")
    question_counter = 1
```

# دالة لحفظ السؤال

def save_question(user_id, username, question, question_id):
try:
global pending_questions
pending_questions[question_id] = {
‘user_id’: user_id,
‘username’: username,
‘question’: question,
‘timestamp’: datetime.now().strftime(’%Y-%m-%d %H:%M:%S’),
‘status’: ‘pending’
}
return True
except Exception as e:
logger.error(f”Error saving question: {e}”)
return False

# دالة البداية

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
user = update.effective_user

```
    if user.id == ADMIN_ID:
        message = (
            "مرحباً بك يا أدمن! 👨‍💼\n\n"
            "الأوامر المتاحة:\n"
            "/pending - الأسئلة المعلقة\n"
            "/stats - الإحصائيات\n"
            "/help - المساعدة"
        )
    else:
        message = (
            f"مرحباً {user.first_name}! 👋\n\n"
            "أنا بوت الأسئلة والأجوبة 🤖\n\n"
            "أرسل سؤالك وسأقوم بتوصيله للمختص! 📝"
        )
    
    await update.message.reply_text(message)
    
except Exception as e:
    logger.error(f"Error in start command: {e}")
    await update.message.reply_text("حدث خطأ، يرجى المحاولة مرة أخرى.")
```

# دالة استقبال الأسئلة

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
global question_counter
user = update.effective_user
question = update.message.text

```
    # إذا كان الأدمن
    if user.id == ADMIN_ID:
        await handle_admin_response(update, context)
        return
    
    # تحديث العداد
    update_question_counter()
    
    # حفظ السؤال
    question_id = f"Q{question_counter}"
    if save_question(user.id, user.username or user.first_name, question, question_id):
        question_counter += 1
        
        # رد للمستخدم
        await update.message.reply_text(
            f"✅ تم استلام سؤالك!\n\n"
            f"🆔 رقم السؤال: {question_id}\n"
            f"⏰ الوقت: {datetime.now().strftime('%H:%M')}\n\n"
            f"سيتم الرد عليك قريباً! 🕐"
        )
        
        # إرسال للأدمن
        admin_message = (
            f"📩 *سؤال جديد!*\n\n"
            f"🆔 `{question_id}`\n"
            f"👤 {user.first_name}"
        )
        if user.username:
            admin_message += f" (@{user.username})"
        admin_message += f"\n🆔 `{user.id}`\n"
        admin_message += f"⏰ {datetime.now().strftime('%H:%M')}\n\n"
        admin_message += f"❓ {question}\n\n"
        admin_message += f"📝 الرد: `{question_id} [الإجابة]`"
        
        # أزرار سريعة
        keyboard = [
            [InlineKeyboardButton("✅ تم الرد", callback_data=f"answered_{question_id}")],
            [InlineKeyboardButton("❌ حذف", callback_data=f"delete_{question_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error sending to admin: {e}")
    else:
        await update.message.reply_text("حدث خطأ في حفظ السؤال، يرجى المحاولة مرة أخرى.")

except Exception as e:
    logger.error(f"Error handling question: {e}")
    await update.message.reply_text("حدث خطأ، يرجى المحاولة مرة أخرى.")
```

# دالة معالجة ردود الأدمن

async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
message = update.message.text

```
    if message.startswith('Q') and ' ' in message:
        parts = message.split(' ', 1)
        question_id = parts[0]
        answer = parts[1]
        
        if question_id in pending_questions:
            question_data = pending_questions[question_id]
            user_id = question_data['user_id']
            original_question = question_data['question']
            
            # إرسال الإجابة للمستخدم
            user_message = (
                f"✅ *تم الرد على سؤالك!*\n\n"
                f"🆔 {question_id}\n"
                f"❓ {original_question}\n\n"
                f"💬 *الإجابة:*\n{answer}\n\n"
                f"⏰ {datetime.now().strftime('%H:%M')}"
            )
            
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=user_message,
                    parse_mode='Markdown'
                )
                
                # تحديث الحالة
                pending_questions[question_id]['status'] = 'answered'
                pending_questions[question_id]['answer'] = answer
                pending_questions[question_id]['answered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                await update.message.reply_text(
                    f"✅ تم إرسال الإجابة بنجاح!\n🆔 {question_id}"
                )
                
            except Exception as e:
                await update.message.reply_text(
                    f"❌ خطأ في الإرسال:\n{str(e)}"
                )
        else:
            available_questions = list(pending_questions.keys())[-5:]  # آخر 5 أسئلة
            await update.message.reply_text(
                f"❌ السؤال {question_id} غير موجود\n\n"
                f"الأسئلة المتاحة: {', '.join(available_questions)}\n\n"
                f"استخدم /pending للأسئلة المعلقة"
            )
    else:
        await update.message.reply_text(
            "📝 *تنسيق الرد:*\n"
            "`Q1 الإجابة هنا`\n\n"
            "استخدم /pending للأسئلة المعلقة",
            parse_mode='Markdown'
        )

except Exception as e:
    logger.error(f"Error handling admin response: {e}")
    await update.message.reply_text("حدث خطأ في معالجة الرد.")
```

# دالة عرض الأسئلة المعلقة

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
if update.effective_user.id != ADMIN_ID:
await update.message.reply_text(“❌ للأدمن فقط!”)
return

```
    pending = {q_id: q_data for q_id, q_data in pending_questions.items() if q_data['status'] == 'pending'}
    
    if not pending:
        await update.message.reply_text("✅ لا توجد أسئلة معلقة!")
        return
    
    message = f"📋 *الأسئلة المعلقة ({len(pending)}):*\n\n"
    
    # ترتيب الأسئلة
    sorted_questions = sorted(pending.items(), key=lambda x: int(x[0][1:]) if x[0][1:].isdigit() else 0)
    
    for q_id, data in sorted_questions[:10]:  # أول 10 أسئلة
        message += f"🆔 `{q_id}` - {data['username']}\n"
        message += f"⏰ {data['timestamp']}\n"
        question_preview = data['question'][:40] + '...' if len(data['question']) > 40 else data['question']
        message += f"❓ {question_preview}\n\n"
    
    if len(pending) > 10:
        message += f"... و {len(pending) - 10} أسئلة أخرى"
    
    await update.message.reply_text(message, parse_mode='Markdown')

except Exception as e:
    logger.error(f"Error showing pending questions: {e}")
    await update.message.reply_text("حدث خطأ في عرض الأسئلة.")
```

# دالة الإحصائيات

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
if update.effective_user.id != ADMIN_ID:
await update.message.reply_text(“❌ للأدمن فقط!”)
return

```
    total = len(pending_questions)
    answered = len([q for q in pending_questions.values() if q['status'] == 'answered'])
    pending = total - answered
    
    percentage = (answered/total*100) if total > 0 else 0
    
    stats_message = (
        f"📊 *إحصائيات البوت:*\n\n"
        f"📝 إجمالي الأسئلة: {total}\n"
        f"✅ تم الرد: {answered}\n"
        f"⏳ في الانتظار: {pending}\n"
        f"📈 معدل الإجابة: {percentage:.1f}%\n"
        f"🔢 العداد التالي: Q{question_counter}"
    )
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')

except Exception as e:
    logger.error(f"Error showing stats: {e}")
    await update.message.reply_text("حدث خطأ في عرض الإحصائيات.")
```

# دالة معالجة الأزرار

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
query = update.callback_query
await query.answer()

```
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ غير مسموح!")
        return
    
    data = query.data
    
    if data.startswith('answered_'):
        question_id = data.split('_')[1]
        if question_id in pending_questions:
            pending_questions[question_id]['status'] = 'answered'
            pending_questions[question_id]['answered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await query.edit_message_text(f"✅ تم تحديد {question_id} كمُجاب عليه")
    
    elif data.startswith('delete_'):
        question_id = data.split('_')[1]
        if question_id in pending_questions:
            del pending_questions[question_id]
            await query.edit_message_text(f"🗑️ تم حذف {question_id}")

except Exception as e:
    logger.error(f"Error handling button: {e}")
```

# دالة المساعدة

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
if update.effective_user.id != ADMIN_ID:
await update.message.reply_text(
“أرسل أي سؤال وسأقوم بتوصيله للمختص! 📝”
)
return

```
    help_text = (
        "🔧 *أوامر الأدمن:*\n\n"
        "/pending - الأسئلة المعلقة\n"
        "/stats - الإحصائيات\n"
        "/help - المساعدة\n\n"
        "📝 *طريقة الرد:*\n"
        "`Q1 الإجابة هنا`\n\n"
        "💡 استخدم الأزرار للإجراءات السريعة"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

except Exception as e:
    logger.error(f"Error in help command: {e}")
    await update.message.reply_text("حدث خطأ في عرض المساعدة.")
```

# دالة معالجة الأخطاء

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
logger.error(“Exception while handling an update:”, exc_info=context.error)

# دالة إيقاف البوت بأمان

def signal_handler(sig, frame):
logger.info(“Shutting down bot…”)
sys.exit(0)

def main():
try:
# تسجيل معالجات الإشارات
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

```
    # تحديث العداد
    update_question_counter()
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pending", show_pending))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    app.add_error_handler(error_handler)
    
    # تشغيل البوت
    logger.info("Bot is starting...")
    logger.info(f"Admin ID: {ADMIN_ID}")
    
    # استخدام polling للبيئات السحابية
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
except Exception as e:
    logger.error(f"Critical error in main: {e}")
    sys.exit(1)
```

if **name** == ‘**main**’:
main()
