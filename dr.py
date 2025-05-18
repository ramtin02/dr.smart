import os
import logging
import requests
from telegram import Update, constants, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ---------- تنظیمات ----------
TELEGRAM_TOKEN = "7059865195:AAF7vAUwLPS-LnomjH1qPLuQzbBozqrOaPI"
GEMINI_API_KEY = "AIzaSyAQMplJDe4bLfcnHXxlMrhFmGmoK-Ly9Qk"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ---------- لاگ ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- دکمه‌ها ----------
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        ["🩺 سوال پزشکی", "💊 اطلاعات دارویی"],
        ["📊 تفسیر آزمایش", "ℹ️ راهنما"],
        ["👤 درباره ربات"]
    ],
    resize_keyboard=True
)

# ---------- پاسخ از Gemini ----------
def get_gemini_response(prompt: str) -> str:
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        if 'candidates' in result and result['candidates']:
            parts = result['candidates'][0]['content']['parts']
            return "\n".join(part.get('text', '') for part in parts)
        return "پاسخی پیدا نشد."
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return "❌ خطا در ارتباط با سامانه هوش مصنوعی."

# ---------- مولد پرامپت پزشکی ----------
def build_medical_prompt(category: str, question: str) -> str:
    intro = "تو یک دستیار پزشکی حرفه‌ای هستی. به سؤال زیر بر اساس دانش پزشکی روز و به زبان ساده پاسخ بده."
    disclaimer = "\n\n⚠️ توجه: پاسخ‌ها صرفاً جهت آگاهی بوده و جایگزین مشاوره با پزشک نیستند."
    if category == "سوال پزشکی":
        return f"{intro}\nسؤال پزشکی:\n{question}{disclaimer}"
    elif category == "اطلاعات دارویی":
        return f"{intro}\nسؤال دارویی:\n{question}{disclaimer}"
    elif category == "تفسیر آزمایش":
        return f"{intro}\nلطفاً این نتیجه آزمایش را تفسیر کن:\n{question}{disclaimer}"
    else:
        return question

# ---------- دستورات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام! من دستیار پزشکی هوشمند هستم. یکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=main_keyboard
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 من می‌تونم به سوالات پزشکی، دارویی و تفسیر آزمایش‌ها کمک کنم.\n"
        "یکی از دکمه‌ها رو انتخاب کن یا مستقیم سوالت رو بنویس!"
    )

# ---------- پردازش پیام ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "ℹ️ راهنما":
        await help_command(update, context)
        return
    elif text == "👤 درباره ربات":
        await update.message.reply_text("🤖 من یک دستیار پزشکی هوشمند هستم. توسط هوش مصنوعی طراحی شدم.")
        return
    elif text in ["🩺 سوال پزشکی", "💊 اطلاعات دارویی", "📊 تفسیر آزمایش"]:
        context.user_data["category"] = text.replace("🩺 ", "").replace("💊 ", "").replace("📊 ", "")
        await update.message.reply_text(f"✍️ لطفاً سوال مربوط به «{context.user_data['category']}» رو بنویس:")
        return

    category = context.user_data.get("category", "سوال پزشکی")
    await update.message.chat.send_action(action=constants.ChatAction.TYPING)
    prompt = build_medical_prompt(category, text)
    response = get_gemini_response(prompt)
    await update.message.reply_text(response)

# ---------- اجرای ربات ----------
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🤖 ربات پزشکی آماده است.")
    application.run_polling()

if __name__ == '__main__':
    main()
