import logging
import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from telegram.request import HTTPXRequest

# تمكين التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# استبدل هذا بالتوكن الخاص بك
TOKEN = "8924369693:AAGQRS7nEUSu4csxmylwc3rNG3v1lNL2iN4"

# تهيئة عميل OpenAI
# API_KEY و API_BASE يتم توفيرهما تلقائياً في بيئة الساندبوكس
client = OpenAI()

# قاموس لتخزين مهام المستخدمين
user_tasks = {}

# دالة لمعالجة أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"مرحباً {user.mention_html()}! أنا بوت التواصل والمساعدة للموظفين والطلاب. أنا هنا لمساعدتك في مهامك اليومية وتقديم الدعم. كيف يمكنني مساعدتك اليوم؟",
    )

# دالة لمعالجة أمر /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "أنا بوت مصمم لمساعدتك في مهامك اليومية والتواصل. إليك بعض الأوامر التي يمكنك استخدامها:\n"
        "/start - لبدء المحادثة والحصول على رسالة ترحيب.\n"
        "/help - لعرض قائمة الأوامر المتاحة.\n"
        "/addtask <مهمة> - لإضافة مهمة إلى قائمة مهامك.\n"
        "/tasks - لعرض جميع مهامك الحالية.\n"
        "/donetask <رقم المهمة> - لوضع علامة على مهمة كمكتملة.\n"
        "/studytips - للحصول على نصائح دراسية مفيدة.\n"
        "يمكنك أيضاً الدردشة معي مباشرة وسأحاول الإجابة على أسئلتك!"
    )

# دالة لإضافة مهمة
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    task_text = " ".join(context.args)
    if not task_text:
        await update.message.reply_text("الرجاء تحديد المهمة التي تريد إضافتها. مثال: /addtask إرسال التقرير")
        return

    if user_id not in user_tasks:
        user_tasks[user_id] = []
    user_tasks[user_id].append(task_text)
    await update.message.reply_text(f"تمت إضافة المهمة: \'{task_text}\'")

# دالة لعرض المهام
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in user_tasks or not user_tasks[user_id]:
        await update.message.reply_text("ليس لديك أي مهام حالياً.")
        return

    tasks_list = "قائمة مهامك:\n"
    for i, task in enumerate(user_tasks[user_id]):
        tasks_list += f"{i+1}. {task}\n"
    await update.message.reply_text(tasks_list)

# دالة لوضع علامة على مهمة كمكتملة
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in user_tasks or not user_tasks[user_id]:
        await update.message.reply_text("ليس لديك أي مهام حالياً لوضع علامة عليها كمكتملة.")
        return

    try:
        task_index = int(context.args[0]) - 1
        if 0 <= task_index < len(user_tasks[user_id]):
            completed_task = user_tasks[user_id].pop(task_index)
            await update.message.reply_text(f"تم وضع علامة على المهمة \'{completed_task}\' كمكتملة!")
        else:
            await update.message.reply_text("رقم مهمة غير صالح. الرجاء استخدام /tasks لعرض أرقام المهام الصحيحة.")
    except (ValueError, IndexError):
        await update.message.reply_text("الرجاء تحديد رقم المهمة لوضع علامة عليها كمكتملة. مثال: /donetask 1")

# دالة لتقديم نصائح دراسية
async def study_tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tips = [
        "قم بإنشاء جدول دراسي والتزم به.",
        "حدد أهدافاً واضحة لكل جلسة دراسية.",
        "خذ فترات راحة منتظمة لتجنب الإرهاق.",
        "راجع المواد بانتظام لتعزيز الذاكرة.",
        "ابحث عن مكان هادئ للدراسة بعيداً عن المشتتات.",
        "استخدم تقنيات دراسية متنوعة مثل الخرائط الذهنية والملخصات.",
        "لا تتردد في طلب المساعدة من المعلمين أو الزملاء عند الحاجة."
    ]
    await update.message.reply_text(f"نصيحة دراسية: {random.choice(tips)}")

# دالة لمعالجة الرسائل النصية العادية باستخدام الذكاء الاصطناعي
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # يمكنك تغيير النموذج هنا إذا أردت
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي ومفيد للموظفين والطلاب. تجيب على الأسئلة وتقدم المساعدة في مجموعة واسعة من المهام."},
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = response.choices[0].message.content
        await update.message.reply_text(ai_response)
    except Exception as e:
        logger.error(f"فشل في الاتصال بـ OpenAI: {e}")
        await update.message.reply_text("عذراً، حدث خطأ أثناء محاولة معالجة طلبك. الرجاء المحاولة مرة أخرى لاحقاً.")

def main() -> None:
    """بدء تشغيل البوت."""
    # إنشاء التطبيق وتمرير توكن البوت الخاص بك مع إعدادات المهلة.
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)
    application = Application.builder().token(TOKEN).request(request).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("addtask", add_task))
    application.add_handler(CommandHandler("tasks", show_tasks))
    application.add_handler(CommandHandler("donetask", done_task))
    application.add_handler(CommandHandler("studytips", study_tips))

    # إضافة معالج للرسائل النصية العادية التي ليست أوامر
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

    # بدء البوت
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
