import logging
import openai
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# إعدادات اللوج
logging.basicConfig(level=logging.INFO)

# أسئلة التحليل
questions = [
    "شنو هواياتك المفضلة؟",
    "تحب تعيش وحدك لو ويا ناس؟",
    "تحب الصخب لو الهدوء؟",
    "توصف نفسك اجتماعي لو منطوي؟",
    "شنو يريحك من التوتر؟",
    "تحب المغامرات لو الاستقرار؟",
    "تنفعل بسرعه لو هادئ؟",
    "شنو أكثر شي يفرحك؟",
    "تحب تتعلم شي جديد؟ شنو هو؟",
    "شنو طموحك؟",
    "تعتمد على مشاعرك لو على المنطق؟",
    "تفضل الليل لو النهار؟",
    "تحب تشتغل ضمن فريق لو وحدك؟",
    "شنو روتينك اليومي؟",
    "اذا زعلت، شلون ترجع تهدأ؟"
]

# لتخزين بيانات المستخدم
user_answers = {}
STATE_ASKING = range(1)

# بدء المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_answers[user_id] = {"answers": [], "current_q": 0}
    await update.message.reply_text("هلو 🌟 راح أسألك 15 سؤال بسيط عن نفسك...\nجاوب بصراحة. نبدأ:\n\n" + questions[0])
    return STATE_ASKING

# استلام الأجوبة
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    answer = update.message.text
    data = user_answers[user_id]
    data["answers"].append(answer)
    data["current_q"] += 1

    if data["current_q"] < len(questions):
        await update.message.reply_text(questions[data["current_q"]])
        return STATE_ASKING
    else:
        # نولد تحليل باستخدام OpenAI
        summary = "\n".join([f"{i+1}. {ans}" for i, ans in enumerate(data["answers"])])
        await update.message.reply_text("شكراً على إجاباتك 🙏 الآن نحلل شخصيتك… ⏳")

        prompt = f"""أنت مساعد نفسي ذكي. المستخدم جاوب على الأسئلة التالية:
{summary}
اعطني تحليل دقيق ومبسط عن شخصية المستخدم، وقدم له نصائح أو مقترحات.
استخدم لهجة عراقية إذا أمكن، وخلّ الكلام حنون ومفيد.
"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content
        await update.message.reply_text("✅ التحليل مالك:\n\n" + result)
        await update.message.reply_text("كدر تسألني بعد أي سؤال تحبّه وأنا أجاوبك حسب شخصيتك 🌟")
        return ConversationHandler.END

# ردود الذكاء الاصطناعي بعد التحليل
async def chat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    prompt = f"""المستخدم عنده تحليلات سابقة عن شخصيته. سؤاله الجديد: {user_input}
جاوبه بناءً على تحليله كشخص منطوي أو اجتماعي وهواياته، بأسلوب ذكي وودي."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    await update.message.reply_text(response.choices[0].message.content)

# أمر /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أوكي لغيت العملية.")
    return ConversationHandler.END

# تشغيل البوت
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_mode))
    print("Bot is running...")
    app.run_polling()
