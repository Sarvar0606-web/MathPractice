"""Telegram'dan kelgan webhook yangilanishlarini (update) qayta ishlash."""
from config import WEBAPP_URL
from bot.i18n import bot_text
from bot.telegram_api import send_message, webapp_keyboard
from db import crud
from webapp.logger import logger


def _user_language(telegram_id: int) -> str:
    user = crud.get_user(telegram_id)
    return (user or {}).get("language") or "uz"


def _handle_start(chat_id: int, user: dict, payload: str):
    telegram_id = user.get("id")
    logger.info("BOT_START user=%s username=%s payload=%s", telegram_id, user.get("username"), payload)

    is_new_referral = False
    if payload.startswith("ref_"):
        referrer_code = payload[len("ref_"):].strip()
        existing = crud.get_user(telegram_id)
        if referrer_code and not existing:
            crud.record_pending_referral(telegram_id, referrer_code)
            is_new_referral = True

    lang = _user_language(telegram_id)

    if not WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
        send_message(chat_id, bot_text(lang, "no_webapp"))
        return

    is_admin = crud.is_admin(telegram_id)
    text = bot_text(lang, "greeting")
    if is_new_referral:
        text += bot_text(lang, "referral_welcome")
    if is_admin:
        text += bot_text(lang, "admin_suffix")

    send_message(chat_id, text, reply_markup=webapp_keyboard(WEBAPP_URL, bot_text(lang, "open_app_btn")))


def _handle_help(chat_id: int, user: dict):
    lang = _user_language(user.get("id"))
    send_message(chat_id, bot_text(lang, "help"))


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
        parts = text.split(maxsplit=1)
        payload = parts[1].strip() if len(parts) > 1 else ""
        _handle_start(chat_id, user, payload)
    elif text.startswith("/help"):
        _handle_help(chat_id, user)
