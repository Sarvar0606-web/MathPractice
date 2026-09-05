"""Bot xabarlarining (Telegram chatiga yuboriladigan matnlar) ko'p tilli
matnlari. Mini App'dagi I18N (static/app.js) dan mustaqil — chunki bot
xabarlari foydalanuvchi Mini App'ni birinchi marta ochib til tanlashidan
OLDIN ham yuborilishi mumkin (masalan /start). Shu sabab, agar foydalanuvchi
ro'yxatdan o'tgan bo'lsa uning saqlangan tilidan, aks holda standart (uz)
tildan foydalaniladi."""

from config import DEFAULT_LANGUAGE

BOT_TEXTS = {
    "uz": {
        "no_webapp": (
            "⚠️ Mini App manzili (WEBAPP_URL) sozlanmagan yoki HTTPS emas.\n"
            "Iltimos, .env faylida WEBAPP_URL ni to'g'ri HTTPS manzilga sozlang."
        ),
        "greeting": (
            "Assalomu alaykum! 👋\n\n"
            "Bu bot orqali matematik testlarni Mini App ichida yechishingiz mumkin.\n"
            "Boshlash uchun quyidagi tugmani bosing 👇"
        ),
        "admin_suffix": "\n\n🛡 Siz admin sifatida barcha foydalanuvchilar natijalarini ko'ra olasiz.",
        "referral_welcome": "\n\n🎁 Do'stingiz taklifi orqali keldingiz!",
        "help": (
            "/start — Mini App'ni ochish uchun tugmani olish\n"
            "Barcha testlar va natijalar Mini App ichida ko'rsatiladi."
        ),
        "open_app_btn": "🧮 Mini App'ni ochish",
        "reminder": (
            "👋 Salom{name}! Bugun MathBot'da bir nechta test yechib, "
            "bilimingizni mustahkamlab qo'ying 💪"
        ),
    },
    "ru": {
        "no_webapp": (
            "⚠️ Адрес Mini App (WEBAPP_URL) не настроен или не HTTPS.\n"
            "Пожалуйста, укажите корректный HTTPS-адрес в файле .env."
        ),
        "greeting": (
            "Здравствуйте! 👋\n\n"
            "С помощью этого бота вы можете решать математические тесты в Mini App.\n"
            "Нажмите кнопку ниже, чтобы начать 👇"
        ),
        "admin_suffix": "\n\n🛡 Вы администратор и можете видеть результаты всех пользователей.",
        "referral_welcome": "\n\n🎁 Вы пришли по приглашению друга!",
        "help": (
            "/start — получить кнопку для открытия Mini App\n"
            "Все тесты и результаты отображаются внутри Mini App."
        ),
        "open_app_btn": "🧮 Открыть Mini App",
        "reminder": (
            "👋 Привет{name}! Сегодня решите пару тестов в MathBot и "
            "закрепите свои знания 💪"
        ),
    },
    "en": {
        "no_webapp": (
            "⚠️ The Mini App address (WEBAPP_URL) is not set or is not HTTPS.\n"
            "Please set a valid HTTPS URL in the .env file."
        ),
        "greeting": (
            "Hello! 👋\n\n"
            "With this bot you can solve math tests inside the Mini App.\n"
            "Tap the button below to get started 👇"
        ),
        "admin_suffix": "\n\n🛡 You are an admin and can see all users' results.",
        "referral_welcome": "\n\n🎁 You joined via a friend's invite!",
        "help": (
            "/start — get the button to open the Mini App\n"
            "All tests and results are shown inside the Mini App."
        ),
        "open_app_btn": "🧮 Open Mini App",
        "reminder": (
            "👋 Hi{name}! Solve a few tests in MathBot today and "
            "keep your skills sharp 💪"
        ),
    },
}


def bot_text(language: str, key: str) -> str:
    lang = language if language in BOT_TEXTS else DEFAULT_LANGUAGE
    return BOT_TEXTS[lang][key]
