"""Telegram'dan kelgan webhook yangilanishlarini (update) qayta ishlash."""
from config import WEBAPP_URL
from bot.telegram_api import send_message, webapp_keyboard
from db import crud
from webapp.logger import logger


def _handle_start(chat_id: int, user: dict):
    logger.info("BOT_START user=%s username=%s", user.get("id"), user.get("username"))

    if not WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
        send_message(
            chat_id,
            "⚠️ Mini App manzili (WEBAPP_URL) sozlanmagan yoki HTTPS emas.\n"
            "Iltimos, .env faylida WEBAPP_URL ni to'g'ri HTTPS manzilga sozlang.",
        )
        return

    is_admin = crud.is_admin(user.get("id"))
    text = (
        "Assalomu alaykum! 👋\n\n"
        "Bu bot orqali matematik testlarni Mini App ichida yechishingiz mumkin.\n"
        "Boshlash uchun quyidagi tugmani bosing 👇"
    )
    if is_admin:
        text += "\n\n🛡 Siz admin sifatida barcha foydalanuvchilar natijalarini ko'ra olasiz."

    send_message(chat_id, text, reply_markup=webapp_keyboard(WEBAPP_URL))


def _handle_help(chat_id: int):
    send_message(
        chat_id,
        "/start — Mini App'ni ochish uchun tugmani olish\n"
        "Barcha testlar va natijalar Mini App ichida ko'rsatiladi.",
    )


def handle_update(update: dict):
    message = update.get("message") or update.get("edited_message")
    if not message:
        return  # boshqa turdagi yangilanishlar (masalan callback_query) hozircha kerak emas

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    user = message.get("from") or {}
    text = (message.get("text") or "").strip()

    if chat_id is None:
        return

    if text.startswith("/start"):
        _handle_start(chat_id, user)
    elif text.startswith("/help"):
        _handle_help(chat_id)
