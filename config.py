"""Loyihaning umumiy sozlamalari (.env fayldan o'qiladi)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = {
    int(x.strip())
    for x in _admin_ids_raw.split(",")
    if x.strip().isdigit()
}

WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")

DEV_SKIP_AUTH = os.getenv("DEV_SKIP_AUTH", "0") == "1"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

# Telegram webhook manzilidagi maxfiy qism (URL'ni taxmin qilib bo'lmasligi
# uchun) va Telegram har bir so'rovda yuboradigan maxfiy tokenni tekshirish
# uchun ham shu qiymat ishlatiladi. .env faylida albatta o'zingizga xos
# tasodifiy matn bilan almashtiring.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "mathbot.db"
LOG_PATH = LOGS_DIR / "mathbot.log"

# Har bir testda nechta savol beriladi
QUESTIONS_PER_TEST = 20

# Ruxsat etilgan xonalar soni (1 xonalidan 5 xonaligacha)
MIN_DIGITS = 1
MAX_DIGITS = 5

# Har bir savol uchun tanlanadigan vaqt variantlari (soniyalarda)
TIME_OPTIONS = [
    {"label": "30 soniya", "seconds": 30},
    {"label": "1 daqiqa", "seconds": 60},
    {"label": "2 daqiqa", "seconds": 120},
    {"label": "3 daqiqa", "seconds": 180},
    {"label": "5 daqiqa", "seconds": 300},
]

# Bosh menyudagi bo'limlar. Har bir amal (OPERATIONS) o'z bo'limiga
# ("section") tegishli — shu orqali frontend menyusi guruhlanadi.
SECTIONS = [
    {
        "key": "arithmetic",
        "label": "Arifmetika",
        "icon": "🧮",
        "color": "#6366f1",
        "desc": "Qo'shish, ayirish, ko'paytirish, bo'lish, solishtirish",
    },
    {
        "key": "fractions",
        "label": "Kasrlar",
        "icon": "🍕",
        "color": "#f43f5e",
        "desc": "Kasrlar ustida amallar",
    },
    {
        "key": "percent",
        "label": "Foizlar",
        "icon": "💯",
        "color": "#f59e0b",
        "desc": "Foizlar bilan bog'liq masalalar",
    },
]

OPERATIONS = {
    "add": {"label": "Qo'shish", "symbol": "+", "color": "#22c55e", "icon": "plus", "section": "arithmetic"},
    "sub": {"label": "Ayirish", "symbol": "−", "color": "#f97316", "icon": "minus", "section": "arithmetic"},
    "mul": {"label": "Ko'paytirish", "symbol": "×", "color": "#3b82f6", "icon": "times", "section": "arithmetic"},
    "div": {"label": "Bo'lish", "symbol": "÷", "color": "#ec4899", "icon": "divide", "section": "arithmetic"},
    "compare": {"label": "Solishtirish", "symbol": "<>", "color": "#8b5cf6", "icon": "compare", "section": "arithmetic"},

    "frac_compare": {"label": "Solishtirish", "symbol": "<>", "color": "#f43f5e", "icon": "compare", "section": "fractions"},
    "frac_simplify": {"label": "Qisqartirish", "symbol": "↓", "color": "#f97316", "icon": "simplify", "section": "fractions"},
    "frac_add": {"label": "Qo'shish", "symbol": "+", "color": "#22c55e", "icon": "plus", "section": "fractions"},
    "frac_sub": {"label": "Ayirish", "symbol": "−", "color": "#eab308", "icon": "minus", "section": "fractions"},
    "frac_mul": {"label": "Ko'paytirish", "symbol": "×", "color": "#3b82f6", "icon": "times", "section": "fractions"},
    "frac_div": {"label": "Bo'lish", "symbol": "÷", "color": "#ec4899", "icon": "divide", "section": "fractions"},
    "frac_mixed": {"label": "Aralash kasr", "symbol": "⇄", "color": "#8b5cf6", "icon": "mixed", "section": "fractions"},
    "frac_decimal": {"label": "O'nli kasr", "symbol": ".", "color": "#06b6d4", "icon": "decimal", "section": "fractions"},

    "percent_of": {"label": "Sonning foizini topish", "symbol": "%", "color": "#f59e0b", "icon": "percent", "section": "percent"},
    "percent_find_whole": {"label": "Foiz bo'yicha sonni topish", "symbol": "%", "color": "#0ea5e9", "icon": "search", "section": "percent"},
    "percent_increase": {"label": "Narx oshishi", "symbol": "↑", "color": "#22c55e", "icon": "increase", "section": "percent"},
    "percent_discount": {"label": "Chegirma", "symbol": "↓", "color": "#ef4444", "icon": "discount", "section": "percent"},
    "percent_profit_loss": {"label": "Foyda/zarar", "symbol": "±", "color": "#8b5cf6", "icon": "scale", "section": "percent"},
    "percent_successive": {"label": "Ketma-ket foiz o'zgarishi", "symbol": "⇄", "color": "#ec4899", "icon": "repeat", "section": "percent"},
}
