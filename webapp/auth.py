"""Telegram Mini App initData imzosini tekshirish (autentifikatsiya)."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from flask import request

from config import BOT_TOKEN, DEV_SKIP_AUTH

MAX_AUTH_AGE_SECONDS = 24 * 60 * 60  # 1 kun


class AuthError(Exception):
    """initData tekshiruvidan o'tmagan so'rovlar uchun."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _validate_init_data(init_data: str) -> dict:
    """Telegram hujjatlashtirishiga ko'ra initData'ni tekshiradi.

    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data:
        raise AuthError(401, "initData yo'q")

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise AuthError(401, "hash topilmadi")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    secret_key = hmac.new(
        b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise AuthError(401, "initData imzosi noto'g'ri")

    auth_date = int(parsed.get("auth_date", "0"))
    if time.time() - auth_date > MAX_AUTH_AGE_SECONDS:
        raise AuthError(401, "initData muddati o'tgan")

    user_raw = parsed.get("user")
    if not user_raw:
        raise AuthError(401, "foydalanuvchi ma'lumoti yo'q")
    return json.loads(user_raw)


def get_current_telegram_user() -> dict:
    """Joriy so'rovdagi Telegram foydalanuvchisini qaytaradi.

    Muvaffaqiyatsiz bo'lsa AuthError ko'taradi — chaqiruvchi shuni ushlab
    JSON xato javobini qaytarishi kerak.
    """
    init_data = request.headers.get("X-Telegram-Init-Data", "")

    if DEV_SKIP_AUTH:
        # Lokal test uchun: header orqali {"id":..,"first_name":..} yuborish mumkin,
        # bo'lmasa standart test foydalanuvchisi ishlatiladi.
        if init_data:
            try:
                return json.loads(init_data)
            except json.JSONDecodeError:
                pass
        return {"id": 1, "first_name": "Test", "username": "test_user"}

    return _validate_init_data(init_data)
