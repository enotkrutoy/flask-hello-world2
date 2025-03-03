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
