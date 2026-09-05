"""MathBot — Flask ilovasi (WSGI). Mini App'ni, API'ni va Telegram webhook'ni
bitta joyda xizmat qiladi — bu PythonAnywhere kabi bepul WSGI hostinglarda
ishlashi uchun maxsus shu tarzda qurilgan (uzluksiz polling shart emas)."""
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory

from config import WEBHOOK_SECRET
from db.database import init_db, close_db
from webapp.api import api_bp
from webapp.logger import logger
from bot.webhook import handle_update

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = Flask(__name__, static_folder=None)
app.teardown_appcontext(close_db)
app.register_blueprint(api_bp)

# Ilova (worker) birinchi marta yuklanganda jadvallar tayyor bo'lishi uchun.
init_db()


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@app.post(f"/webhook/{WEBHOOK_SECRET}")
def telegram_webhook():
    # Telegram har bir so'rovda shu sarlavhani (header) yuboradi — u
    # setWebhook chaqirilganda ro'yxatdan o'tkazilgan secret_token bilan bir
    # xil bo'lishi kerak. Bu boshqa birov shu manzilga soxta so'rov
    # yubormasligini ta'minlaydi.
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not WEBHOOK_SECRET or token != WEBHOOK_SECRET:
        return jsonify({"ok": False}), 403

    update = request.get_json(silent=True) or {}
    try:
        handle_update(update)
    except Exception:
        logger.exception("Webhook yangilanishini qayta ishlashda xatolik")
    return jsonify({"ok": True})


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})


# PythonAnywhere'ning WSGI konfiguratsiya fayli odatda `application`
# nomli obyektni qidiradi.
application = app


if __name__ == "__main__":
    from config import HOST, PORT
    app.run(host=HOST, port=PORT, debug=False)
