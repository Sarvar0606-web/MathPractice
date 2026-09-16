"""2+ kundan beri test yechmagan foydalanuvchilarga eslatma xabar yuboradi
VA (bir yo'la) ma'lumotlar bazasidan avtomatik zaxira nusxa oladi.

Bu skript alohida, mustaqil ishga tushiriladi (Flask serveridan tashqarida) —
PythonAnywhere'ning "Tasks" bo'limida kuniga bir marta (masalan har kuni
soat 09:00 da) ishga tushirish uchun sozlanadi:

    python3.12 /home/USERNAME/MathBot/send_reminders.py

Bepul PythonAnywhere akkauntida kuniga BITTA rejalashtirilgan vazifa
(scheduled task) slot mavjud — shu sabab kunlik zaxira nusxa olish
(backup_db.py) ham ayni shu skript ichida, eslatmalar bilan bir vaqtda
bajariladi (alohida "Tasks" slot band qilinmaydi).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask  # noqa: E402

from backup_db import backup_database  # noqa: E402
from bot.i18n import bot_text  # noqa: E402
from bot.telegram_api import send_message  # noqa: E402
from db import crud  # noqa: E402
from db.database import close_db, init_db  # noqa: E402
from webapp.logger import logger  # noqa: E402

# db/crud.py get_db() Flask 'g' obyektiga tayanadi — shu sabab skriptni ham
# minimal Flask ilova konteksti ichida ishga tushiramiz.
_app = Flask(__name__)
_app.teardown_appcontext(close_db)


def main():
    init_db()
    with _app.app_context():
        users = crud.inactive_users(days=2)
        sent = 0
        for u in users:
            name = f", {u['first_name']}" if u.get("first_name") else ""
            text = bot_text(u.get("language") or "uz", "reminder").format(name=name)
            try:
                send_message(u["telegram_id"], text)
                sent += 1
            except Exception:
                logger.exception("Eslatma yuborishda xatolik: user=%s", u["telegram_id"])
        logger.info("REMINDERS_SENT count=%s / topildi=%s", sent, len(users))
        print(f"{sent} ta foydalanuvchiga eslatma yuborildi (jami nofaol: {len(users)}).")

    try:
        backup_path = backup_database()
        if backup_path:
            print(f"Zaxira nusxa yaratildi: {backup_path.name}")
    except Exception:
        logger.exception("Zaxira nusxa olishda xatolik")


if __name__ == "__main__":
    main()
