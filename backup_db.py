"""SQLite ma'lumotlar bazasidan avtomatik zaxira nusxa (backup) oladi.

Bu modul mustaqil ishlamaydi — PythonAnywhere bepul akkauntida kuniga
faqat BITTA rejalashtirilgan vazifa (scheduled task) slot mavjud, va u
allaqachon send_reminders.py tomonidan band qilingan. Shu sabab backup
funksiyasi shu yerga alohida modul sifatida chiqarilgan va
send_reminders.py o'zining kunlik ishga tushishida uni ham chaqiradi
(1 kunlik "Tasks" slotidan ikkala vazifa uchun ham foydalaniladi).

Zaxira fayllari data/backups/ papkasiga sana bilan saqlanadi va disk
joyidan tejash uchun oxirgi BACKUP_KEEP_COUNT ta faylgina saqlab qolinadi
(eskilari avtomatik o'chiriladi)."""
import datetime
import shutil
from pathlib import Path
from typing import Optional

from config import DB_PATH
from webapp.logger import logger

BACKUP_DIR = DB_PATH.parent / "backups"
BACKUP_KEEP_COUNT = 14  # oxirgi 14 kunlik zaxira saqlanadi


def backup_database() -> Optional[Path]:
    """DB faylining joriy holatini backups/ papkasiga nusxalaydi va
    eskirgan zaxiralarni tozalaydi. Muvaffaqiyatli bo'lsa yangi fayl
    yo'lini, DB fayli mavjud bo'lmasa None qaytaradi."""
    if not DB_PATH.exists():
        logger.warning("BACKUP_SKIP: DB fayli topilmadi (%s)", DB_PATH)
        return None

    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    dest = BACKUP_DIR / f"mathbot_{stamp}.db"
    # DIQQAT: shutil.copy (copy2 EMAS) ishlatiladi — copy2 manba faylning
    # mtime'ini nusxaga ham ko'chiradi, natijada barcha zaxiralar BIR XIL
    # mtime'ga ega bo'lib qolishi (agar manba DB fayli ikki backup orasida
    # o'zgarmagan bo'lsa) va quyidagi tozalash funksiyasi noto'g'ri
    # (tasodifiy) fayllarni o'chirib yuborishi mumkin edi.
    shutil.copy(DB_PATH, dest)
    logger.info("BACKUP_OK fayl=%s hajmi=%s bayt", dest.name, dest.stat().st_size)

    _prune_old_backups()
    return dest


def _prune_old_backups() -> None:
    # Fayl nomi "mathbot_YYYY-MM-DD_HHMMSS.db" formatida — lug'aviy
    # (alphabetical) tartiblash xronologik tartibga to'g'ri keladi.
    # mtime asosida emas, aynan shu tarzda tartiblanadi, chunki
    # shutil.copy (copy2 emas) fayl yaratilish vaqtini emas, balki hozirgi
    # vaqtni beradi — lekin baribir nom bo'yicha tartiblash ishonchliroq.
    backups = sorted(BACKUP_DIR.glob("mathbot_*.db"), key=lambda p: p.name, reverse=True)
    for old in backups[BACKUP_KEEP_COUNT:]:
        try:
            old.unlink()
            logger.info("BACKUP_PRUNE eskirgan fayl o'chirildi: %s", old.name)
        except OSError:
            logger.exception("BACKUP_PRUNE xatolik: %s", old.name)


if __name__ == "__main__":
    result = backup_database()
    if result:
        print(f"Zaxira nusxa yaratildi: {result}")
    else:
        print("Zaxira nusxa yaratilmadi (DB fayli topilmadi).")
