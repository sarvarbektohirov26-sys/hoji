"""
Хочи — бот-ассистент для Telegram на Google Gemini.
Запуск: python bot.py

Переменные окружения:
BOT_TOKEN=...
GEMINI_API_KEY=...
BOT_NAME=Хочи
MODEL=gemini-2.5-flash
MAX_HISTORY=20
"""

import logging
import os
import re
import time
import traceback
from collections import defaultdict, deque

from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Хочи")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
MAX_HISTORY = max(2, int(os.getenv("MAX_HISTORY", "20")))

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise SystemExit("Не найден BOT_TOKEN или GEMINI_API_KEY в переменных окружения.")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    f"Ты — {BOT_NAME}, дружелюбный и умный ассистент в Telegram. "
    "Отвечай по-русски, кратко и по делу."
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("khochi")

# История хранится отдельно для каждого пользователя в каждом чате.
histories = defaultdict(lambda: defaultdict(lambda: deque(maxlen=MAX_HISTORY)))
last_request = defaultdict(float)


def is_spam(user_id: int) -> bool:
    now = time.time()
    if now - last_request[user_id] < 3:
        return True
    last_request[user_id] = now
    return False


def mentioned(update: Update) -> bool:
    msg = update.effective_message
    if not msg or not msg.text:
        return False

    if BOT_NAME and BOT_NAME.casefold() in msg.text.casefold():
        return True

    replied = msg.reply_to_message
    return bool(
        replied
        and replied.from_user
        and replied.from_user.is_bot
    )


def clean_text(update: Update) -> str:
    msg = update.effective_message
    text = msg.text or ""
    if BOT_NAME:
        text = re.sub(re.escape(BOT_NAME), "", text, flags=re.IGNORECASE)
    return text.strip(" ,.!?\\n\\t")


async def ask_gemini(chat_id: int, user_id: int, user_text: str) -> str:
    history = histories[chat_id][user_id]
    history.append({"role": "user", "content": user_text})

    contents = [
        {
            "role": "user" if item["role"] == "user" else "model",
            "parts": [{"text": item["content"]}],
        }
        for item in history
    ]

    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=contents,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
            },
        )
        answer = response.text
        if not answer:
            raise RuntimeError("Gemini вернул пустой ответ.")
        history.append({"role": "assistant", "content": answer})
        return answer
    except Exception as exc:
        log.error("Gemini error: %s", exc)
        log.error(traceback.format_exc())
        # Удаляем только последнее сообщение пользователя, если оно всё ещё последнее.
        if history and history[-1]["role"] == "user":
            history.pop()
        return (
            "⚠️ Не удалось получить ответ от Gemini. "
            "Проверь модель MODEL и доступность API-ключа в Google AI Studio. "
            "Подробности есть в логах Railway."
        )


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"Привет! Я — {BOT_NAME} 🤖\\n\\n"
        "В личке просто пиши мне — отвечу на вопросы.\\n"
        "В группе окликни меня по имени или ответь на моё сообщение.\\n\\n"
        "Команды:\\n"
        "/clear — забыть историю диалога\\n"
        "/help — справка"
    )
    if update.effective_message:
        await update.effective_message.reply_text(text)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, ctx)


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat and update.effective_user and update.effective_message:
        histories[update.effective_chat.id].pop(update.effective_user.id, None)
        await update.effective_message.reply_text("🧹 История диалога очищена.")


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not msg.text or not chat or not user:
        return

    if chat.type in ("group", "supergroup") and not mentioned(update):
        return

    if is_spam(user.id):
        await msg.reply_text("⏳ Не так быстро, дай подумать 🙂")
        return

    text = clean_text(update) if chat.type in ("group", "supergroup") else msg.text.strip()
    if not text:
        await msg.reply_text("Да, я тут! Слушаю 👂")
        return

    await msg.chat.send_action(action="typing")
    answer = await ask_gemini(chat.id, user.id, text)

    for start in range(0, len(answer), 4000):
        await msg.reply_text(answer[start : start + 4000])


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    log.info("%s запущен! Модель: %s", BOT_NAME, MODEL)
    app.run_polling()


if __name__ == "__main__":
    main()
