"""
Хочи — бот-ассистент для Telegram на бесплатной модели Google Gemini.
Запуск: python bot.py
"""

import os
import logging
import time
import traceback
from collections import defaultdict, deque

import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Хочи")
MODEL = os.getenv("MODEL", "gemini-1.5-flash")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise SystemExit("Не найден BOT_TOKEN или GEMINI_API_KEY в файле .env")

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel(model_name=MODEL, system_instruction="Ты — Хочи, дружелюбный умный ассистент в Telegram. Отвечай по-русски, кратко и по делу.")

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
log = logging.getLogger("khochi")

# История: {chat_id: {user_id: deque сообщений}}
histories = defaultdict(lambda: defaultdict(lambda: deque(maxlen=MAX_HISTORY)))

last_request = defaultdict(float)


def to_gemini_format(history):
    """Переводит нашу историю в формат Gemini (роли user/model)."""
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [msg["content"]]})
    return contents


async def ask_gemini(update, user_text):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    histories[chat_id][user_id].append({"role": "user", "content": user_text})
    try:
        resp = await gemini.generate_content_async(to_gemini_format(histories[chat_id][user_id]))
        answer = resp.text
        histories[chat_id][user_id].append({"role": "assistant", "content": answer})
        return answer
    except Exception as e:
        log.error(f"Gemini error: {e}")
        log.error(traceback.format_exc())
        histories[chat_id][user_id].pop()
        return f"⚠️ Ошибка API: {e}"


def is_spam(user_id):
    now = time.time()
    if now - last_request[user_id] < 3:
        return True
    last_request[user_id] = now
    return False


def mentioned(update):
    msg = update.effective_message
    if not msg or not msg.text:
        return False
    if BOT_NAME.lower() in msg.text.lower():
        return True
    if msg.reply_to_message and msg.reply_to_message.from_user and msg.reply_to_message.from_user.is_bot:
        return True
    return False


def clean_text(update):
    text = update.effective_message.text
    return text.replace(BOT_NAME, ).replace(BOT_NAME.lower(), ).strip(" ,.")


async def cmd_start(update, ctx):
    text = (
        f"Привет! Я — {BOT_NAME} 🤖\n\n"
        "В личке просто пиши мне — отвечу как ChatGPT.\n"
        "В группе окликни меня по имени («Хочи, ...») или ответь на моё сообщение.\n\n"
        "Команды:\n"
        "/clear — забыть историю диалога\n"
        "/help — справка"
    )
    await update.message.reply_text(text)


async def cmd_help(update, ctx):
    await cmd_start(update, ctx)


async def cmd_clear(update, ctx):
    histories[update.effective_chat.id].pop(update.effective_user.id, None)
    await update.message.reply_text("🧹 История диалога очищена.")


async def handle_message(update, ctx):
    if not update.message or not update.message.text:
        return
    chat = update.effective_chat
    user = update.effective_user
    if chat.type in ("group", "supergroup") and not mentioned(update):
        return
    if is_spam(user.id):
        await update.message.reply_text("⏳ Не так быстро, дай подумать 🙂")
        return
    if chat.type in ("group", "supergroup"):
        text = clean_text(update)
    else:
        text = update.message.text
    if not text:
        await update.message.reply_text("Да, я тут! Слушаю 👂")
        return
    await update.message.chat.send_action(action="typing")
    answer = await ask_gemini(update, text)
    for i in range(0, len(answer), 4000):
        await update.message.reply_text(answer[i:i + 4000])


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info(f"{BOT_NAME} запущен! Модель: {MODEL}")
    app.run_polling()

if __name__ == "__main__":
    main()