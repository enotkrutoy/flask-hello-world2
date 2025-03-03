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

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токены и ключи
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HF_API_KEY = os.getenv('HF_API_KEY')

async def escape_markdown_v2(text):
    """Экранирует специальные символы для MarkdownV2."""
    escape_chars = re.escape(r'!*()[]{}#+"\'')
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

async def start(update: Update, context: CallbackContext):
    """Ответ на команду /start."""
    await update.effective_message.reply_text(
        'Привет! Я готов помочь вам. Напишите, что вас интересует.'
    )

async def handle_message(update: Update, context: CallbackContext):
    """Обработка входящих сообщений."""
    text = update.message.text
    # Генерация ответа с использованием API Hugging Face
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api-inference.huggingface.co/pipeline/feature-extraction/',
            headers={'Authorization': f'Bearer {HF_API_KEY}'},
            json={'inputs': text}
        ) as response:
            data = await response.json()
            # Обработка данных и формирование ответа
            reply = f'Ответ на ваше сообщение: {data}'
            await update.effective_message.reply_text(reply)

async def fetch_with_retries(url, params=None, data=None, headers=None):
    """Запрос с повторами."""
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.request(
                    method='GET',
                    url=url,
                    params=params,
                    data=data,
                    headers=headers
                ) as response:
                    return await response.json()
            except aiohttp.ClientError as e:
                if attempt == 2:
                    logger.error(f'Ошибка при запросе: {e}')
                    return None

async def clear_history(update: Update, context: CallbackContext):
    """Очистка истории."""
    context.user_data.clear()
    await update.effective_message.reply_text('История очищена.')

async def view_history(update: Update, context: CallbackContext):
    """Просмотр истории."""
    history = context.user_data.get('history', [])
    if not history:
        await update.effective_message.reply_text('История пуста.')
    else:
        await update.effective_message.reply_text(
            'История:\n' + '\n'.join(history)
        )

async def set_system_prompt(update: Update, context: CallbackContext):
    """Установка системного промпта."""
    prompt = update.message.text.split(' ', 1)[1]
    context.user_data['system_prompt'] = prompt
    await update.effective_message.reply_text('Системный промпт установлен.')

async def handle_document(update: Update, context: CallbackContext):
    """Обработка документов."""
    document = update.message.document
    await update.effective_message.reply_text(
        f'Принят документ: {document.file_name}'
    )

async def handle_voice(update: Update, context: CallbackContext):
    """Обработка голосовых сообщений."""
    voice = update.message.voice
    await update.effective_message.reply_text(
        'Принято голосовое сообщение.'
    )

def main():
    # Создание приложения бота
    application = ApplicationBuilder().token(TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('clear', clear_history))
    application.add_handler(CommandHandler('history', view_history))
    application.add_handler(CommandHandler('set_system_prompt', set_system_prompt))

    # Регистрация обработчиков сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document, handle_document))
    application.add_handler(MessageHandler(filters.Voice, handle_voice))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

5. Настройка приложения Flask

В файле app.py добавьте следующий код:


from flask import Flask, request, jsonify
from bot import main as bot_main

app = Flask(__name__)

@app.route('/api/telegram', methods=['POST'])
def handle_telegram_update():
    update = request.get_json()
    # Обработка обновлений от Telegram
    # Здесь должна быть логика обработки обновлений
    # Для примера просто возвращаем подтверждение
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)
