from flask import Flask, render_template, jsonify
import os
import logging

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")

# Проверка наличия ключей
if not HF_API_KEY or not TELEGRAM_BOT_TOKEN:
    logger.error("Необходимые переменные окружения отсутствуют.")
    exit(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    status = {
        "bot_active": True,
        "last_update": "2023-10-01T12:00:00Z",
        "errors": [],
        "system_prompt": "помощник"
    }
    return jsonify(status)

if __name__ == '__main__':
    app.run(debug=True)
