from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from bot import main as bot_main
import os
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_tokens', methods=['POST'])
def set_tokens():
    telegram_bot_token = request.form['telegram_bot_token']
    huggingface_api_key = request.form['huggingface_api_key']
    
    # Сохранение токенов в переменные окружения
    os.environ['TELEGRAM_BOT_TOKEN'] = telegram_bot_token
    os.environ['HF_API_KEY'] = huggingface_api_key
    
    # Перезапуск бота
    bot_main()
    
    flash('Токены успешно установлены и бот перезапущен.', 'success')
    return redirect(url_for('index'))

@app.route('/check_connection', methods=['POST'])
def check_connection():
    try:
        # Проверка соединения с Hugging Face API
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct") as response:
                response.raise_for_status()
                data = await response.json()
        
        if "model" in data:
            flash('Соединение с Hugging Face API установлено.', 'success')
        else:
            flash('Ошибка соединения с Hugging Face API.', 'danger')
    except aiohttp.ClientError as e:
        logger.error(f"Сетевая ошибка: {e}")
        flash(f'Сетевая ошибка: {e}', 'danger')
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        flash(f'Неизвестная ошибка: {e}', 'danger')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
