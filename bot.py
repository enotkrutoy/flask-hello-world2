import re
import aiohttp
import logging
import os
from telegram import Update, ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import speech_recognition as sr
from io import BytesIO

# Загрузка переменных из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токены и ключи из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

# Проверка наличия ключей
if not HF_API_KEY or not TELEGRAM_BOT_TOKEN:
    logger.error("Необходимые переменные окружения отсутствуют.")
    exit(1)

# Hugging Face URL
HF_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct/v1/chat/completions"
DEFAULT_SYSTEM_PROMPT = "помощник"

def escape_markdown_v2(text):
    """
    Экранирует специальные символы для использования в блоках кода MarkdownV2.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!$&@"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для ответов на ваши вопросы. Напишите мне что-нибудь.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if not user_message:
        await update.message.reply_text("Пожалуйста, отправьте текстовое сообщение.")
        return
    await update.message.reply_text("👀 Думаю... 🐇🐇🐇")
    system_prompt = context.user_data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.5,
        "max_tokens": 2048,
        "top_p": 0.7,
        "stream": False,
    }
    try:
        data = await fetch_with_retries(HF_API_URL, headers, payload)
        choices = data.get("choices")
        if not choices or "message" not in choices[0]:
            await update.message.reply_text("Пожалуйста, попробуйте позже.")
            logger.error(f"Некорректный ответ от API: {data}")
            return
        reply = choices[0].get("message", {}).get("content", "")
        if not reply:
            await update.message.reply_text("К сожалению, я не смог придумать ответа.")
            return
        # Проверка на слишком длинный ответ
        if len(reply) > 4096:
            # Если ответ слишком длинный, разделим его на части
            chunks = [reply[i:i+4096] for i in range(0, len(reply), 4096)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            # Если ответ подходит по длине, отправляем его целиком
            if "```" in reply:
                # Экранируем символы Markdown в тексте
                escaped_reply = escape_markdown_v2(reply)
                code_block = f"```\n{escaped_reply}\n```"
                await update.message.reply_text(code_block, parse_mode="MarkdownV2")
            else:
                await update.message.reply_text(reply)
    except aiohttp.ClientError as e:
        logger.error(f"Сетевая ошибка: {e}")
        await update.message.reply_text(f"Сетевая ошибка: {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await update.message.reply_text(f"Неизвестная ошибка: {e}")

async def fetch_with_retries(url, headers, json, retries=3):
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=json) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            if attempt == retries - 1:
                logger.error(f"Ошибка при запросе: {e}")
                raise
            logger.warning(f"Попытка {attempt + 1} не удалась, повторяю...")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("История диалога очищена.")

async def view_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = context.user_data.get("history", [])
    if not history:
        await update.message.reply_text("История диалога пуста.")
    else:
        history_text = "\n".join(history)
        await update.message.reply_text(f"История диалога:\n{history_text}")

async def set_system_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите системный промпт.")
        return
    system_prompt = " ".join(context.args)
    context.user_data["system_prompt"] = system_prompt
    await update.message.reply_text(f"Системный промпт установлен: {system_prompt}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document or document.mime_type != "text/plain":
        await update.message.reply_text("Пожалуйста, отправьте текстовый файл.")
        return
    file = await document.get_file()
    file_content = await file.download_as_string()
    await update.message.reply_text(f"Содержимое файла:\n{file_content}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    if not voice:
        await update.message.reply_text("Пожалуйста, отправьте голосовое сообщение.")
        return
    file = await voice.get_file()
    file_content = await file.download_as_bytearray()
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(BytesIO(file_content))
    with audio_file as source:
        audio_data = recognizer.record(source)
    text = recognizer.recognize_google(audio_data, language="ru-RU")
    await update.message.reply_text(f"Текст: {text}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("history", view_history))
    app.add_handler(CommandHandler("set_system_prompt", set_system_prompt))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    logger.info("Бот запущен!")
    app.run_polling()
