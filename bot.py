import logging
import sys
import signal
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# الإعدادات
BOT_TOKEN = "7750811448:AAHP0G9tkIwNxWyvyO2H0t5U25Df6_dTrI"
ADMIN_ID = 8011237487  # نوعه int مش str

# إعداد السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# تخزين الأسئلة
pending_questions = {}
question_counter = 1

def update_question_counter():
    global question_counter
    try:
        if pending_questions:
            existing_numbers = [int(q[1:]) for q in pending_questions if q.startswith('Q') and q[1:].isdigit()]
            question_counter = max(existing_numbers) + 1 if existing_numbers else 1
        else:
            question_counter = 1
    except Exception as e:
        logger.error(f"Error updating question counter: {e}")
        question_counter = 1

def save_question(user_id, username, question, question_id):
    try:
        pending_questions[question_id] = {
            'user_id': user_id,
            'username': username,
            'question': question,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'pending'
        }
        return True
    except Exception as e:
        logger.error(f"Error saving question: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "مرحباً بك يا أدمن!\n\n"
            "/pending - عرض الأسئلة\n"
            "/stats - عرض الإحصائيات\n"
            "/help - تعليمات الاستخدام"
        )
    else:
        await update.message.reply_text(
            f"مرحباً {user.first_name}!\n\n"
            "أرسل سؤالك وسأقوم بتوصيله للمختص!"
        )

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global question_counter
    user = update.effective_user
    question = update.message.text

    if user.id == ADMIN_ID:
        await handle_admin_response(update, context)
        return

    update_question_counter()
    question_id = f"Q{question_counter}"
    if save_question(user.id, user.username or user.first_name, question, question_id):
        question_counter += 1

        await update.message.reply_text(
            f"✅ تم استلام سؤالك!\nرقم السؤال: {question_id}"
        )

        admin_message = (
            f"📩 سؤال جديد:\n\n"
            f"🆔 {question_id}\n"
            f"👤 {user.first_name} (@{user.username})\n"
            f"❓ {question}"
        )

        keyboard = [
            [InlineKeyboardButton("✅ تم الرد", callback_data=f"answered_{question_id}")],
            [InlineKeyboardButton("❌ حذف", callback_data=f"delete_{question_id}")]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message.text
        if message.startswith("Q") and ' ' in message:
            q_id, answer = message.split(' ', 1)
            if q_id in pending_questions:
                user_id = pending_questions[q_id]['user_id']
                question = pending_questions[q_id]['question']
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🆔 {q_id}\n❓ {question}\n💬 الإجابة:\n{answer}"
                )
                pending_questions[q_id]['status'] = 'answered'
                pending_questions[q_id]['answer'] = answer
                pending_questions[q_id]['answered_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                await update.message.reply_text("✅ تم إرسال الرد.")
            else:
                await update.message.reply_text("❌ لم يتم العثور على السؤال.")
    except Exception as e:
        logger.error(f"Error in admin response: {e}")
        await update.message.reply_text("حدث خطأ.")

async def show_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ غير مسموح.")
        return

    pending = {k: v for k, v in pending_questions.items() if v['status'] == 'pending'}

    if not pending:
        await update.message.reply_text("✅ لا توجد أسئلة معلقة.")
        return

    message = "📋 الأسئلة المعلقة:\n\n"
    for q_id, data in pending.items():
        message += f"{q_id} - {data['username']}\n"

    await update.message.reply_text(message)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ غير مسموح.")
        return

    total = len(pending_questions)
    answered = len([1 for q in pending_questions.values() if q['status'] == 'answered'])
    pending = total - answered
    percentage = (answered / total) * 100 if total > 0 else 0

    await update.message.reply_text(
        f"📊 الإحصائيات:\n"
        f"إجمالي: {total}\n"
        f"✅ تم الرد: {answered}\n"
        f"⏳ معلق: {pending}\n"
        f"📈 معدل الإجابة: {percentage:.1f}%"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ غير مسموح.")
        return

    data = query.data
    if data.startswith("answered_"):
        q_id = data.split("_")[1]
        if q_id in pending_questions:
            pending_questions[q_id]['status'] = 'answered'
            await query.edit_message_text(f"✅ تم الرد على {q_id}")
    elif data.startswith("delete_"):
        q_id = data.split("_")[1]
        if q_id in pending_questions:
            del pending_questions[q_id]
            await query.edit_message_text(f"🗑️ تم حذف {q_id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❓ أرسل سؤالك وسيتم الرد عليك قريباً.")
        return

    await update.message.reply_text(
        "/pending - الأسئلة المعلقة\n"
        "/stats - عرض الإحصائيات\n"
        "/help - عرض التعليمات\n\n"
        "📝 للرد على سؤال: Q1 الإجابة"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling update:", exc_info=context.error)

def signal_handler(sig, frame):
    logger.info("Shutting down bot...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    update_question_counter()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pending", show_pending))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    app.add_error_handler(error_handler)

    logger.info("Bot started.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
