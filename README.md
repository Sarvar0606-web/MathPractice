# MathBot — Matematik testlar Telegram Mini App

Telegram bot + Mini App: foydalanuvchi ro'yxatdan o'tadi (F.I.O. va tug'ilgan
sana), so'ng Arifmetika, Kasrlar, Foizlar, Algebra, Funksiyalar, Geometriya,
Ehtimollik va statistika hamda Mantiqiy masalalar bo'limlarida (1–5
murakkablik darajasi, har biri 20 tadan savol, 4 variantli javob, har savol
uchun tanlangan vaqt bilan) testlar yechadi. Interfeys o'zbek, rus va ingliz
tillarida ishlaydi. Natijalar saqlanadi; foydalanuvchi o'z natijalari,
kunlik seriyasi, yutuqlari va reytingdagi o'rnini, admin esa barcha
foydalanuvchilar natijalarini batafsil (va Excel formatida) ko'ra oladi.

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
+ `openpyxl` (admin panelning Excel eksporti uchun) — hammasi sof Python
yoki keng qo'llab-quvvatlanadigan paketlar, hech qanday Rust/C++
kompilyatsiyasi kerak emas (Windows'da eski `aiohttp`/`pydantic-core`
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
- `BOT_USERNAME` — (ixtiyoriy) botning username'i (@ belgisiz). To'ldirilsa,
  "Do'stni taklif qilish" bo'limida to'liq ulashiladigan havola (`t.me/...`)
  chiqadi; bo'sh qoldirilsa faqat referral kodi ko'rsatiladi.
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

### Nofaol foydalanuvchilarga eslatma (ixtiyoriy, tavsiya etiladi)

2+ kundan beri test yechmagan foydalanuvchilarga bot avtomatik eslatma
xabari yuborishi uchun `send_reminders.py` skripti mavjud. PythonAnywhere'ning
**Tasks** bo'limida (bepul akkauntda kuniga 1 ta vazifa mavjud) quyidagicha
sozlang:

```
python3.12 /home/USERNAME/MathBot/send_reminders.py
```

Vaqtni xohlagancha tanlashingiz mumkin (masalan har kuni ertalab). Skript
ishga tushganda o'zi mustaqil ishlaydi — Flask serverini alohida talab
qilmaydi.

## Foydalanish oqimi (Mini App ichida)

1. Botga `/start` yuboring → "Mini App'ni ochish" tugmasi chiqadi.
2. Mini App birinchi marta ochilganda til tanlash ekrani chiqadi: 🇺🇿 O'zbekcha,
   🇷🇺 Русский, 🇬🇧 English. Tanlangan til foydalanuvchi profiliga saqlanadi
   (ro'yxatdan o'tgandan keyin), shuning uchun keyingi safar Mini App
   avtomatik shu tilda ochiladi. Istalgan ekranning yuqori o'ng burchagidagi
   bayroqcha tugmasi orqali tilni xohlagan vaqtda o'zgartirish mumkin —
   o'zgarish darhol interfeys va savol matnlariga ta'sir qiladi.
3. Birinchi marta kirganda: Ism, Familiya, Otasining ismi va tug'ilgan sana
   so'raladi.
4. Bosh menyudan bo'lim tanlanadi:
   - **Arifmetika** → qo'shish/ayirish/ko'paytirish/bo'lish/solishtirish/
     amal tartibi/qoldiqli bo'lish/manfiy sonlar → sonlar xonasini (1–5) →
     vaqtni tanlaysiz. "Solishtirish"da javob variantlari `<`, `>`, `=`
     belgilaridan iborat. "Amal tartibi" va "Manfiy sonlar" bir nechta
     amalli ifodalar ko'rinishida (masalan `(a+b) × (c-d)`), "Qoldiqli
     bo'lish" esa javobni "bo'linma qoldiq qism" shaklida (masalan
     `7 qoldiq 3`) so'raydi.
   - **Kasrlar** → oddiy kasr/solishtirish/qisqartirish/qo'shish/ayirish/
     ko'paytirish/bo'lish/aralash kasrga aylantirish/o'nli kasrga
     aylantirish → murakkablik darajasini (1–5) → vaqtni tanlaysiz.
     Javoblar kasr ko'rinishida (masalan `3/4`, `2 1/3`, `0.75`) beriladi.
   - **Foizlar** → sonning foizini topish/foiz bo'yicha sonni topish/narx
     oshishi/chegirma/foyda-zarar/ketma-ket foiz o'zgarishi → murakkablik
     darajasini (1–5) → vaqtni tanlaysiz. Savollar so'z masalasi (matnli)
     shaklida beriladi.
   - **Algebra** → tenglama/tengsizlik/qavs ochish/soddalashtirish/
     darajalar/ildizlar/sistemalar → murakkablik darajasini (1–5) →
     vaqtni tanlaysiz. Tenglama darajasi oshgani sayin ko'rinishi ham
     murakkablashadi (masalan 1-daraja: `x + 5 = 12`, 5-daraja:
     `3(2x - 5) - 4(x + 2) = 17`).
   - **Funksiyalar** → chiziqli funksiya/kvadrat funksiya/grafik (y kesish
     nuqtasi)/funksiya qiymatini topish/nol nuqtalar → murakkablik
     darajasini (1–5) → vaqtni tanlaysiz. Savollar so'z masalasi
     shaklida beriladi (masalan "y = 2x - 5 funksiyaning x = 3 dagi
     qiymatini toping.").
   - **Geometriya** → perimetr/yuza/hajm/uchburchak/to'rtburchak/aylana/
     Pifagor teoremasi/burchaklar → murakkablik darajasini (1–5) → vaqtni
     tanlaysiz. Savollar geometrik so'z masalasi shaklida beriladi
     (masalan "Tomonlari 5 va 8 bo'lgan to'g'ri to'rtburchakning
     perimetrini toping.").
   - **Ehtimollik va statistika** → o'rtacha qiymat/mediana/moda/ehtimollik/
     kombinatorika → murakkablik darajasini (1–5) → vaqtni tanlaysiz.
     O'rtacha qiymat/mediana/moda savollari 4–6 tadan sonlar ro'yxati
     bilan so'z masalasi shaklida beriladi, ehtimollik javobi kasr
     ko'rinishida (masalan `3/10`), kombinatorika esa faktorial (n!)
     asosidagi joylashtirishlar sonini so'raydi.
   - **Mantiqiy masalalar** → ketma-ketlik/ortiqchasini topish/yosh
     masalalari/taqqoslash → murakkablik darajasini (1–5) → vaqtni
     tanlaysiz. Ketma-ketlikda keyingi son (masalan `2, 5, 8, 11, ?`),
     ortiqchasini topishda 4 sondan qaysi biri boshqalarga mos
     kelmasligi (masalan multiple/juft-toq/kvadrat sonlar bo'yicha),
     yosh masalalarida ikkita "bola"ning yoshlari orasidagi bog'liqlik,
     taqqoslashda esa `A > B`, `B > C` kabi bir nechta shart asosida eng
     katta/kichigini topish so'raladi.
   Barcha bo'limlarda ham 20 tadan savol, 4 variantli javob va tasdiqlash
   dialogi bir xil ishlaydi.
5. **Til**: interfeys matnlari, mavzu/bo'lim nomlari va so'z masalalari
   (foizlar, geometriya, funksiyalar, statistika, mantiqiy masalalar)
   tanlangan tilga mos tarjima qilinadi. Matematik ifodalar (arifmetika,
   kasrlar, tenglamalar) allaqachon til-neytral bo'lgani uchun o'zgarmaydi.
   Bot xabarlari (`/start`, `/help`, eslatmalar) ham endi foydalanuvchining
   saqlangan tiliga mos (uz/ru/en) yuboriladi — faqat foydalanuvchi hali
   ro'yxatdan o'tmagan bo'lsa, standart o'zbek tilida ko'rsatiladi.
6. 20 ta savol ketma-ket chiqadi, har birida 4 ta variant bor. Variant
   tanlanganda "Tasdiqlaysizmi yoki qayta o'ylab ko'rasizmi?" so'raladi.
   Tasdiqlangach javob to'g'ri (yashil) yoki xato (qizil, to'g'ri javob
   ko'rsatiladi) ekanligi chiqadi; xato yoki vaqt tugagan javoblarda,
   ba'zi mavzular uchun (foizlar, geometriya, funksiyalar, statistika,
   darajalar/ildizlar, qoldiqli bo'lish, mantiqiy masalalar) qisqacha
   **yechim formulasi** ham ko'rsatiladi. Istalgan vaqtda pastdagi
   **"Testni tugatish"** tugmasi bilan testni erta yakunlash mumkin —
   javob berilmagan savollar hisoblanmaydi.
7. Test tugagach umumiy natija va batafsil (har bir savol bo'yicha) ko'rinish
   mavjud; agar shu safar seriya oshgan yoki yangi yutuq qo'lga kiritilgan
   bo'lsa, natija sahifasida shu haqda alohida xabar chiqadi.
8. **Natijalarim** — barcha o'tilgan testlar tarixi.
9. **Statistikam** (bosh menyudagi yangi bo'lim) — bitta ekranda:
   - 🔥 **Kunlik seriya** — necha kun ketma-ket test yechilgani (joriy va
     eng uzun seriya). Bir kunda bir nechta test yechish seriyani faqat
     bir marta oshiradi; kun o'tkazib yuborilsa seriya 1 ga tushadi.
   - 🏆 **Reyting** — jami to'g'ri javoblar soni bo'yicha o'z o'rningiz va
     to'liq reytingni (eng yaxshi 10 nafar) ko'rish tugmasi.
   - **Mavzular bo'yicha natija** — har bir bo'lim (Arifmetika, Kasrlar va
     h.k.) bo'yicha to'g'ri javob foizi.
   - **Yutuqlar** — 8 ta yutuq: birinchi test, 3/7/30 kunlik seriyalar,
     50/200/1000 ta to'g'ri javob va mukammal natija (20/20). Qo'lga
     kiritilganlari yorqin, qolganlari xira ko'rinadi.
   - 🎁 **Do'stni taklif qilish** — shaxsiy referral kodi (va agar
     `BOT_USERNAME` sozlangan bo'lsa, to'liq ulashiladigan havola) hamda
     shu havola orqali qo'shilgan do'stlar soni.
   - Sonlar xonasi/daraja tanlash ekranida, oldingi natijalar asosida
     (85%+ to'g'ri bo'lsa — bir daraja yuqoriroq, 50%dan past bo'lsa —
     bir daraja pastroq) mos darajaga **"✨ Tavsiya"** belgisi chiqadi.
10. **Admin panel** (faqat `ADMIN_IDS`dagi foydalanuvchilarga ko'rinadi) —
   barcha foydalanuvchilar ro'yxati, har birining testlari soni, jami
   to'g'ri/xato sonlari; foydalanuvchini bosib uning har bir testini,
   testni bosib esa savol-javob tafsilotlarini ko'rish mumkin. Yuqoridagi
   **"Excel formatida yuklab olish"** tugmasi orqali barcha foydalanuvchilar
   ro'yxatini (ism, username, testlar soni, to'g'ri/xato, seriya) `.xlsx`
   fayl sifatida yuklab olish mumkin.

## Loyiha tuzilishi

```
mathbot/
├── app.py                     # Flask ilovasi (WSGI) — hammasi shu yerdan boshlanadi
├── set_webhook.py              # Deploy'dan keyin bir marta ishga tushiriladi
├── send_reminders.py            # Nofaol foydalanuvchilarga eslatma (kunlik scheduled task)
├── config.py                    # .env dan sozlamalarni o'qish
├── bot/
│   ├── telegram_api.py            # Telegram Bot API'ga oddiy HTTP so'rovlar
│   ├── webhook.py                  # Kiruvchi update'larni (masalan /start) qayta ishlash
│   └── i18n.py                     # Bot xabarlarining uz/ru/en matnlari
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

Yangi test turi qo'shish uchun:
1. `logic/` ichida yangi generator yozing.
2. `config.py`dagi `OPERATIONS`ga o'xshash yangi konfiguratsiya tuzing yoki
   yangi bo'lim uchun alohida config qo'shing.
3. `webapp/api.py`da mos endpoint, `static/app.js`da mos ekran qo'shing.

Struktura shunga moslab qurilgan — asosiy menyuga yangi `menu-row` qo'shish
va shu bo'limga mos rang/icon berish yetarli.
