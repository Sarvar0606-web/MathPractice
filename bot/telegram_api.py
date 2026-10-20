"""Telegram Bot API bilan oddiy HTTP orqali ishlash (aiogram shart emas)."""
import requests

from config import BOT_TOKEN

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_message(chat_id: int, text: str, reply_markup: dict | None = None) -> dict:
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    resp = requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=10)
    return resp.json()


def webapp_keyboard(url: str, button_text: str = "🧮 Mini App'ni ochish") -> dict:
    return {
        "inline_keyboard": [[
            {"text": button_text, "web_app": {"url": url}},
        ]]
    }


def set_chat_menu_button(url: str, text: str = "Ochish") -> dict:
    """Mini App'ni 'Menu' tugmasi o'rniga o'rnatadi — bu tugma Telegram'da
    xabar yozish maydonining chap tomonida DOIMIY ko'rinib turadi va bir
    marta bosish bilan (hatto /start yubormasdan ham) Mini App'ni ochadi.
    chat_id ko'rsatilmagani uchun BARCHA foydalanuvchilar uchun standart
    (default) qiymat sifatida o'rnatiladi."""
    resp = requests.post(
        f"{API_BASE}/setChatMenuButton",
        json={"menu_button": {"type": "web_app", "text": text, "web_app": {"url": url}}},
        timeout=15,
    )
    return resp.json()


def set_webhook(url: str, secret_token: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/setWebhook",
        json={"url": url, "secret_token": secret_token, "drop_pending_updates": True},
        timeout=15,
    )
    return resp.json()


def get_webhook_info() -> dict:
    resp = requests.get(f"{API_BASE}/getWebhookInfo", timeout=15)
    return resp.json()
