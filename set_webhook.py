"""Botni deploy qilgandan so'ng BIR MARTA ishga tushiriladigan skript.

Bu skript Telegram'ga: "yangilanishlarni (updates) shu manzilga yubor" deb
xabar beradi. WEBAPP_URL sizning doimiy HTTPS manzilingiz bo'lishi kerak
(masalan https://sizningusername.pythonanywhere.com).

Ishlatish:
    python set_webhook.py           # webhookni o'rnatadi
    python set_webhook.py --info    # joriy webhook holatini ko'rsatadi
    python set_webhook.py --delete  # webhookni o'chiradi (masalan qayta
                                     # lokal test qilish uchun)
"""
import sys

from config import BOT_TOKEN, WEBAPP_URL, WEBHOOK_SECRET
from bot.telegram_api import set_webhook, get_webhook_info, set_chat_menu_button
import requests


def main():
    if not BOT_TOKEN:
        print("XATOLIK: .env faylida BOT_TOKEN sozlanmagan.")
        sys.exit(1)

    if "--info" in sys.argv:
        print(get_webhook_info())
        return

    if "--delete" in sys.argv:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", timeout=15
        )
        print(resp.json())
        return

    if not WEBAPP_URL or not WEBAPP_URL.startswith("https://"):
        print("XATOLIK: .env faylida WEBAPP_URL to'g'ri HTTPS manzil emas.")
        sys.exit(1)
    if not WEBHOOK_SECRET:
        print("XATOLIK: .env faylida WEBHOOK_SECRET bo'sh. Tasodifiy matn kiriting.")
        sys.exit(1)

    url = f"{WEBAPP_URL}/webhook/{WEBHOOK_SECRET}"
    result = set_webhook(url, WEBHOOK_SECRET)
    print(result)
    if result.get("ok"):
        print(f"\n✅ Webhook muvaffaqiyatli o'rnatildi: {url}")
    else:
        print("\n❌ Webhook o'rnatilmadi — yuqoridagi xabarni tekshiring.")
        return

    # Mini App'ni "Menu" tugmasi sifatida ham o'rnatamiz — shunda xabar
    # yozish maydonining yonida doimiy "Ochish" tugmasi chiqadi va
    # foydalanuvchi /start yubormasdan ham Mini App'ni ocha oladi.
    menu_result = set_chat_menu_button(WEBAPP_URL)
    if menu_result.get("ok"):
        print("✅ Chat menu tugmasi ('Ochish') o'rnatildi.")
    else:
        print(f"⚠️  Chat menu tugmasini o'rnatib bo'lmadi: {menu_result}")


if __name__ == "__main__":
    main()
