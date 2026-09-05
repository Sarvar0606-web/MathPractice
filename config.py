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

# Do'stni taklif qilish (referral) havolasi uchun bot username (@ belgisiz).
# Bo'sh qoldirilsa, referral kodi ko'rsatiladi-yu, lekin to'liq havola
# tuzilmaydi (frontend shunga qarab moslashadi).
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# Mini App qo'llab-quvvatlaydigan tillar.
SUPPORTED_LANGUAGES = ["uz", "ru", "en"]
DEFAULT_LANGUAGE = "uz"

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
    {
        "key": "algebra",
        "label": "Algebra",
        "icon": "🧮",
        "color": "#0ea5e9",
        "desc": "Tenglama, tengsizlik, ifodalar bilan ishlash",
    },
    {
        "key": "geometry",
        "label": "Geometriya",
        "icon": "📐",
        "color": "#10b981",
        "desc": "Perimetr, yuza, hajm va boshqa masalalar",
    },
    {
        "key": "functions",
        "label": "Funksiyalar",
        "icon": "📈",
        "color": "#3b82f6",
        "desc": "Chiziqli va kvadrat funksiyalar bilan ishlash",
    },
    {
        "key": "statistics",
        "label": "Ehtimollik va statistika",
        "icon": "🎲",
        "color": "#ec4899",
        "desc": "O'rtacha qiymat, mediana, ehtimollik va boshqalar",
    },
    {
        "key": "logic",
        "label": "Mantiqiy masalalar",
        "icon": "🧩",
        "color": "#7c3aed",
        "desc": "Ketma-ketlik, ortiqchasini topish, yosh va taqqoslash masalalari",
    },
]

# Yutuqlar (achievements) — kalitlar; matn/ikonka frontendda (app.js I18N)
# tilga qarab ko'rsatiladi, backend faqat kalit va shartni biladi.
ACHIEVEMENTS = [
    "first_test", "streak_3", "streak_7", "streak_30",
    "correct_50", "correct_200", "correct_1000", "perfect_score",
]

OPERATIONS = {
    "add": {"label": "Qo'shish", "symbol": "+", "color": "#22c55e", "icon": "plus", "section": "arithmetic"},
    "sub": {"label": "Ayirish", "symbol": "−", "color": "#f97316", "icon": "minus", "section": "arithmetic"},
    "mul": {"label": "Ko'paytirish", "symbol": "×", "color": "#3b82f6", "icon": "times", "section": "arithmetic"},
    "div": {"label": "Bo'lish", "symbol": "÷", "color": "#ec4899", "icon": "divide", "section": "arithmetic"},
    "compare": {"label": "Solishtirish", "symbol": "<>", "color": "#8b5cf6", "icon": "compare", "section": "arithmetic"},
    "arith_order": {"label": "Amal tartibi", "symbol": "()", "color": "#14b8a6", "icon": "order", "section": "arithmetic"},
    "arith_remainder": {"label": "Qoldiqli bo'lish", "symbol": "÷", "color": "#a855f7", "icon": "remainder", "section": "arithmetic"},
    "arith_negative": {"label": "Manfiy sonlar", "symbol": "±", "color": "#64748b", "icon": "negative", "section": "arithmetic"},

    "frac_compare": {"label": "Solishtirish", "symbol": "<>", "color": "#f43f5e", "icon": "compare", "section": "fractions"},
    "frac_simplify": {"label": "Qisqartirish", "symbol": "↓", "color": "#f97316", "icon": "simplify", "section": "fractions"},
    "frac_add": {"label": "Qo'shish", "symbol": "+", "color": "#22c55e", "icon": "plus", "section": "fractions"},
    "frac_sub": {"label": "Ayirish", "symbol": "−", "color": "#eab308", "icon": "minus", "section": "fractions"},
    "frac_mul": {"label": "Ko'paytirish", "symbol": "×", "color": "#3b82f6", "icon": "times", "section": "fractions"},
    "frac_div": {"label": "Bo'lish", "symbol": "÷", "color": "#ec4899", "icon": "divide", "section": "fractions"},
    "frac_mixed": {"label": "Aralash kasr", "symbol": "⇄", "color": "#8b5cf6", "icon": "mixed", "section": "fractions"},
    "frac_decimal": {"label": "O'nli kasr", "symbol": ".", "color": "#06b6d4", "icon": "decimal", "section": "fractions"},
    "frac_basic": {"label": "Oddiy kasr", "symbol": "a/b", "color": "#22c55e", "icon": "basic", "section": "fractions"},

    "percent_of": {"label": "Sonning foizini topish", "symbol": "%", "color": "#f59e0b", "icon": "percent", "section": "percent"},
    "percent_find_whole": {"label": "Foiz bo'yicha sonni topish", "symbol": "%", "color": "#0ea5e9", "icon": "search", "section": "percent"},
    "percent_increase": {"label": "Narx oshishi", "symbol": "↑", "color": "#22c55e", "icon": "increase", "section": "percent"},
    "percent_discount": {"label": "Chegirma", "symbol": "↓", "color": "#ef4444", "icon": "discount", "section": "percent"},
    "percent_profit_loss": {"label": "Foyda/zarar", "symbol": "±", "color": "#8b5cf6", "icon": "scale", "section": "percent"},
    "percent_successive": {"label": "Ketma-ket foiz o'zgarishi", "symbol": "⇄", "color": "#ec4899", "icon": "repeat", "section": "percent"},

    "algebra_equation": {"label": "Tenglama", "symbol": "x=", "color": "#0ea5e9", "icon": "equation", "section": "algebra"},
    "algebra_inequality": {"label": "Tengsizlik", "symbol": "><", "color": "#6366f1", "icon": "inequality", "section": "algebra"},
    "algebra_expand": {"label": "Qavs ochish", "symbol": "()", "color": "#f97316", "icon": "expand", "section": "algebra"},
    "algebra_simplify": {"label": "Soddalashtirish", "symbol": "=", "color": "#22c55e", "icon": "simplify", "section": "algebra"},
    "algebra_exponent": {"label": "Darajalar", "symbol": "^", "color": "#ec4899", "icon": "power", "section": "algebra"},
    "algebra_root": {"label": "Ildizlar", "symbol": "√", "color": "#8b5cf6", "icon": "root", "section": "algebra"},
    "algebra_system": {"label": "Sistemalar", "symbol": "x,y", "color": "#eab308", "icon": "system", "section": "algebra"},

    "geo_perimeter": {"label": "Perimetr", "symbol": "P", "color": "#10b981", "icon": "perimeter", "section": "geometry"},
    "geo_area": {"label": "Yuza", "symbol": "S", "color": "#06b6d4", "icon": "area", "section": "geometry"},
    "geo_volume": {"label": "Hajm", "symbol": "V", "color": "#3b82f6", "icon": "volume", "section": "geometry"},
    "geo_triangle": {"label": "Uchburchak", "symbol": "△", "color": "#f59e0b", "icon": "triangle", "section": "geometry"},
    "geo_quad": {"label": "To'rtburchak", "symbol": "▱", "color": "#f97316", "icon": "quad", "section": "geometry"},
    "geo_circle": {"label": "Aylana", "symbol": "○", "color": "#8b5cf6", "icon": "circle", "section": "geometry"},
    "geo_pythagoras": {"label": "Pifagor teoremasi", "symbol": "√", "color": "#ec4899", "icon": "pythagoras", "section": "geometry"},
    "geo_angles": {"label": "Burchaklar", "symbol": "∠", "color": "#22c55e", "icon": "angles", "section": "geometry"},

    "func_linear": {"label": "Chiziqli funksiya", "symbol": "y=kx+b", "color": "#3b82f6", "icon": "linear", "section": "functions"},
    "func_quadratic": {"label": "Kvadrat funksiya", "symbol": "y=ax²", "color": "#6366f1", "icon": "quadratic", "section": "functions"},
    "func_graph": {"label": "Grafik", "symbol": "📈", "color": "#0ea5e9", "icon": "graph", "section": "functions"},
    "func_value": {"label": "Funksiya qiymatini topish", "symbol": "f(x)", "color": "#22c55e", "icon": "value", "section": "functions"},
    "func_zeros": {"label": "Nol nuqtalar", "symbol": "f(x)=0", "color": "#ef4444", "icon": "zeros", "section": "functions"},

    "stat_mean": {"label": "O'rtacha qiymat", "symbol": "x̄", "color": "#f59e0b", "icon": "mean", "section": "statistics"},
    "stat_median": {"label": "Mediana", "symbol": "Me", "color": "#8b5cf6", "icon": "median", "section": "statistics"},
    "stat_mode": {"label": "Moda", "symbol": "Mo", "color": "#ec4899", "icon": "mode", "section": "statistics"},
    "stat_probability": {"label": "Ehtimollik", "symbol": "P", "color": "#06b6d4", "icon": "probability", "section": "statistics"},
    "stat_combinatorics": {"label": "Kombinatorika", "symbol": "n!", "color": "#f97316", "icon": "combinatorics", "section": "statistics"},

    "logic_sequence": {"label": "Ketma-ketlik", "symbol": "…", "color": "#7c3aed", "icon": "sequence", "section": "logic"},
    "logic_odd_one_out": {"label": "Ortiqchasini toping", "symbol": "≠", "color": "#db2777", "icon": "odd", "section": "logic"},
    "logic_age": {"label": "Yosh masalalari", "symbol": "👤", "color": "#059669", "icon": "age", "section": "logic"},
    "logic_comparison": {"label": "Taqqoslash", "symbol": "><", "color": "#2563eb", "icon": "comparison", "section": "logic"},
}
