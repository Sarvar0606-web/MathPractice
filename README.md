# MathBot — Matematik testlar Telegram Mini App

Telegram bot + Mini App: foydalanuvchi ro'yxatdan o'tadi (F.I.O. va tug'ilgan
sana), so'ng "Arifmetika" bo'limida qo'shish / ayirish / ko'paytirish /
bo'lish bo'yicha (1–5 xonali sonlar, har biri 20 tadan savol, 4 variantli
javob, har savol uchun tanlangan vaqt bilan) testlar yechadi. Natijalar
saqlanadi, foydalanuvchi o'z natijalarini, admin esa barcha foydalanuvchilar
natijalarini batafsil ko'ra oladi.

## Texnologiyalar

- **Backend**: Flask (WSGI) — bot ham, Mini App API'si ham shu bitta ilova
  ichida. Telegram bilan **webhook** orqali ishlaydi (doimiy polling emas),
  shuning uchun PythonAnywhere kabi bepul WSGI hostinglarda ishlaydi.
- **Telegram bilan aloqa**: oddiy HTTP so'rovlar (`requests` kutubxonasi) —
  aiogram yoki boshqa og'ir kutubxona shart emas.
- **Ma'lumotlar bazasi**: SQLite (`data/mathbot.db`)
- **Frontend**: vanilla HTML/CSS/JS (Telegram WebApp SDK), `static/` papkasida
- **Log**: `logs/mathbot.log` fayliga yoziladi (konsolga ham chiqadi)

Ushbu stack ataylab shunday tanlangan: `Flask` + `requests` + `python-dotenv`
— hammasi sof Python yoki keng qo'llab-quvvatlanadigan paketlar, hech qanday
Rust/C++ kompilyatsiyasi kerak emas (Windows'da eski `aiohttp`/`pydantic-core`
bilan bo'lgan muammolar shu sabab butunlay yo'qoladi).

## Loyihani noldan ishga tushirish (lokal, PowerShell)

```powershell
cd D:\Projects\MathBot
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

`.env` faylida:
- `BOT_TOKEN` — @BotFather'dan olingan token.
- `ADMIN_IDS` — admin Telegram ID(lar)i.
- `WEBAPP_URL` — hozircha bo'sh/namuna qoldirsa ham bo'ladi, deploy qilingach
  to'ldiriladi.
- `WEBHOOK_SECRET` — o'zingiz o'ylab topgan tasodifiy matn.
- `DEV_SKIP_AUTH=1` — faqat lokal, brauzerda sinash uchun (Telegram initData
  tekshiruvini o'chirib turadi). Productionda albatta `0`.

Lokal ishga tushirish:
```powershell
python app.py
```
Brauzerda `http://localhost:8080` ochiladi (Mini App). `DEV_SKIP_AUTH=1`
bo'lsa, Telegram'siz ham ko'rish mumkin, lekin bot xabar yubormaydi (buning
uchun webhook orqali haqiqiy HTTPS manzil kerak).

## Doimiy (24/7) ishlashi uchun deploy qilish

Bot kompyuteringiz o'chirilganda ham ishlashi uchun uni internetga doimiy
ulangan bir joyga (masalan PythonAnywhere'ning bepul rejasiga) joylashtirish
kerak. Bu haqda to'liq bosqichma-bosqich qo'llanma alohida taqdim etilgan —
GitHub'ga yuklashdan tortib, PythonAnywhere'da sozlash va webhookni
ro'yxatdan o'tkazishgacha.

Qisqacha oqim:
1. Kodni GitHub'ga yuklaysiz (GitHub Desktop orqali).
2. PythonAnywhere'da bepul akkaunt ochib, konsoldan repo'ni `git clone`
   qilasiz, `pip install -r requirements.txt --user` bajarasiz.
3. "Web" bo'limida yangi web-app yaratib, WSGI faylini `app.py`'dagi
   `application` obyektiga yo'naltirasiz, `/static/` uchun static fayl
   xaritasini qo'shasiz.
4. `.env` faylini serverda ham to'ldirasiz (endi `WEBAPP_URL` — sizning
   PythonAnywhere domeningiz, masalan `https://username.pythonanywhere.com`).
5. **Bir marta** `python set_webhook.py` ni ishga tushirib, Telegram'ga
   "yangilanishlarni shu manzilga yubor" deb aytasiz.
6. Botni Telegram'da sinaysiz.

Kelajakda kodni yangilashda: kompyuteringizda o'zgartirasiz → GitHub
Desktop orqali commit + push → PythonAnywhere konsolida `git pull` →
Web-app sahifasida **Reload** tugmasini bosasiz.

## Foydalanish oqimi (Mini App ichida)

1. Botga `/start` yuboring → "Mini App'ni ochish" tugmasi chiqadi.
2. Birinchi marta kirganda: Ism, Familiya, Otasining ismi va tug'ilgan sana
   so'raladi.
3. Bosh menyudan bo'lim tanlanadi:
   - **Arifmetika** → qo'shish/ayirish/ko'paytirish/bo'lish/solishtirish →
     sonlar xonasini (1–5) → vaqtni tanlaysiz. "Solishtirish"da javob
     variantlari `<`, `>`, `=` belgilaridan iborat.
   - **Kasrlar** → solishtirish/qisqartirish/qo'shish/ayirish/ko'paytirish/
     bo'lish/aralash kasrga aylantirish/o'nli kasrga aylantirish → murakkablik
     darajasini (1–5) → vaqtni tanlaysiz. Javoblar kasr ko'rinishida
     (masalan `3/4`, `2 1/3`, `0.75`) beriladi.
   - **Foizlar** → sonning foizini topish/foiz bo'yicha sonni topish/narx
     oshishi/chegirma/foyda-zarar/ketma-ket foiz o'zgarishi → murakkablik
     darajasini (1–5) → vaqtni tanlaysiz. Savollar so'z masalasi (matnli)
     shaklida beriladi.
   Har uchala bo'limda ham 20 tadan savol, 4 variantli javob va tasdiqlash
   dialogi bir xil ishlaydi.
4. 20 ta savol ketma-ket chiqadi, har birida 4 ta variant bor. Variant
   tanlanganda "Tasdiqlaysizmi yoki qayta o'ylab ko'rasizmi?" so'raladi.
   Tasdiqlangach javob to'g'ri (yashil) yoki xato (qizil, to'g'ri javob
   ko'rsatiladi) ekanligi chiqadi. Vaqt tugasa, javob "xato" hisoblanadi.
   Istalgan vaqtda pastdagi **"Testni tugatish"** tugmasi bilan testni erta
   yakunlash mumkin — javob berilmagan savollar hisoblanmaydi.
5. Test tugagach umumiy natija va batafsil (har bir savol bo'yicha) ko'rinish
   mavjud.
6. **Natijalarim** — barcha o'tilgan testlar tarixi.
7. **Admin panel** (faqat `ADMIN_IDS`dagi foydalanuvchilarga ko'rinadi) —
   barcha foydalanuvchilar ro'yxati, har birining testlari soni, jami
   to'g'ri/xato sonlari; foydalanuvchini bosib uning har bir testini,
   testni bosib esa savol-javob tafsilotlarini ko'rish mumkin.

## Loyiha tuzilishi

```
mathbot/
├── app.py                     # Flask ilovasi (WSGI) — hammasi shu yerdan boshlanadi
├── set_webhook.py              # Deploy'dan keyin bir marta ishga tushiriladi
├── config.py                    # .env dan sozlamalarni o'qish
├── bot/
│   ├── telegram_api.py            # Telegram Bot API'ga oddiy HTTP so'rovlar
│   └── webhook.py                  # Kiruvchi update'larni (masalan /start) qayta ishlash
├── webapp/
│   ├── api.py                  # barcha /api/* endpointlar (Flask blueprint)
│   ├── auth.py                  # Telegram initData tekshiruvi
│   └── logger.py                  # fayl logger
├── db/
│   ├── database.py            # SQLite ulanish va sxema
│   └── crud.py                 # ma'lumotlar bilan ishlash
├── logic/question_generator.py  # misollarni generatsiya qilish
├── static/                   # Mini App frontend (HTML/CSS/JS)
└── data/, logs/                # runtime papkalar (avtomatik yaratiladi)
```

## Qo'shimcha bo'lim qo'shish

Yangi test turi (masalan "Geometriya") qo'shish uchun:
1. `logic/` ichida yangi generator yozing.
2. `config.py`dagi `OPERATIONS`ga o'xshash yangi konfiguratsiya tuzing yoki
   yangi bo'lim uchun alohida config qo'shing.
3. `webapp/api.py`da mos endpoint, `static/app.js`da mos ekran qo'shing.

Struktura shunga moslab qurilgan — asosiy menyuga yangi `menu-row` qo'shish
va shu bo'limga mos rang/icon berish yetarli.
