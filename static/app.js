// MathBot Mini App — frontend logikasi (vanilla JS, SPA)

const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

const INIT_DATA = tg ? tg.initData : "";

const appEl = document.getElementById("app");

const OP_EMOJI = {
  add: "➕", sub: "➖", mul: "✖️", div: "➗", compare: "⚖️",
  frac_compare: "⚖️", frac_simplify: "↓", frac_add: "➕", frac_sub: "➖",
  frac_mul: "✖️", frac_div: "➗", frac_mixed: "🔄", frac_decimal: "🔢",
  percent_of: "💯", percent_find_whole: "🔎", percent_increase: "📈",
  percent_discount: "🏷️", percent_profit_loss: "⚖️", percent_successive: "🔁",
  algebra_equation: "🟰", algebra_inequality: "🔀", algebra_expand: "🧩",
  algebra_simplify: "✨", algebra_exponent: "🔟", algebra_root: "√",
  algebra_system: "🔗",
  geo_perimeter: "📏", geo_area: "🟩", geo_volume: "📦", geo_triangle: "🔺",
  geo_quad: "🔷", geo_circle: "⭕", geo_pythagoras: "📐", geo_angles: "∠",
  arith_order: "🧮", arith_remainder: "➗", arith_negative: "➖", frac_basic: "🍰",
  func_linear: "📈", func_quadratic: "🌐", func_graph: "🗺️", func_value: "🔣",
  func_zeros: "0️⃣",
  stat_mean: "📊", stat_median: "🎚️", stat_mode: "🏆", stat_probability: "🎲",
  stat_combinatorics: "🔢",
  logic_sequence: "🔢", logic_odd_one_out: "🧐", logic_age: "👤", logic_comparison: "⚖️",
};

const SUPERSCRIPT_DIGITS = { 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
function superscript(n) {
  return String(n).split("").map((d) => SUPERSCRIPT_DIGITS[d] !== undefined ? SUPERSCRIPT_DIGITS[d] : d).join("");
}

// ---------- Funksiyalar uchun til-neytral polinom formatlash ----------
function formatPolyTerm(value, suffix) {
  if (suffix === "") return String(Math.abs(value));
  const mag = Math.abs(value);
  return mag === 1 ? suffix : `${mag}${suffix}`;
}

function formatQuadraticExpr(a, b, c) {
  const terms = [];
  if (a !== 0) terms.push({ v: a, suf: "x²" });
  if (b !== 0) terms.push({ v: b, suf: "x" });
  if (c !== 0 || terms.length === 0) terms.push({ v: c, suf: "" });
  let out = "";
  terms.forEach((term, i) => {
    const body = formatPolyTerm(term.v, term.suf);
    if (i === 0) out += term.v < 0 ? `-${body}` : body;
    else out += term.v < 0 ? ` - ${body}` : ` + ${body}`;
  });
  return out;
}

function formatLinearExpr(k, b) {
  return formatQuadraticExpr(0, k, b);
}

// Bu amallarning javob variantlari bitta belgi/qisqa satr (masalan "<", ">", "=")
// bo'lgani uchun javob tugmalarida kattaroq shrift ishlatiladi.
const BIG_CHOICE_OPS = new Set(["compare", "frac_compare"]);

// Bular to'liq gap (masala) shaklida so'raladi — matn kichikroq va chapga
// tekislangan holda ko'rsatiladi.
const WORD_PROBLEM_OPS = new Set([
  "percent_of", "percent_find_whole", "percent_increase",
  "percent_discount", "percent_profit_loss", "percent_successive",
  "geo_perimeter", "geo_area", "geo_volume", "geo_triangle",
  "geo_quad", "geo_circle", "geo_pythagoras", "geo_angles",
  "frac_basic",
  "func_linear", "func_quadratic", "func_graph", "func_value", "func_zeros",
  "stat_mean", "stat_median", "stat_mode", "stat_probability", "stat_combinatorics",
  "logic_age", "logic_comparison",
]);

// "= ?" qo'shilmaydigan amallar (natija emas, aylantirish/qisqartirish so'raladi,
// javob solishtirish belgisi bo'ladi, yoki savol allaqachon "?" bilan tugaydi)
const NO_SUFFIX_OPS = new Set([
  "compare", "frac_compare", "frac_simplify", "frac_mixed", "frac_decimal",
  ...WORD_PROBLEM_OPS,
]);

// ============================================================
// TIL (i18n)
// ============================================================

const LANGS = ["uz", "ru", "en"];
const LANG_META = {
  uz: { flag: "🇺🇿", name: "O'zbekcha" },
  ru: { flag: "🇷🇺", name: "Русский" },
  en: { flag: "🇬🇧", name: "English" },
};
const LANG_STORAGE_KEY = "mathbot_lang";

let LANG = "uz";

const I18N = {
  uz: {
    genericError: "Xatolik yuz berdi",
    loading: "Yuklanmoqda...",
    openInTelegram: "Iltimos, botni Telegram ichida oching.",
    chooseLanguageTitle: "Tilni tanlang",
    chooseLanguageSubtitle: "Ilova tilini tanlang",
    registerTitle: "Ro'yxatdan o'tish",
    registerSubtitle: "Testlarni boshlashdan oldin ma'lumotlaringizni kiriting",
    firstNameLabel: "Ism",
    firstNamePlaceholder: "Ismingiz",
    lastNameLabel: "Familiya",
    lastNamePlaceholder: "Familiyangiz",
    fatherNameLabel: "Otasining ismi (Sharif)",
    fatherNamePlaceholder: "Otangizning ismi",
    dayLabel: "Kun",
    monthLabel: "Oy",
    yearLabel: "Yil",
    fillAllFields: "Iltimos, barcha maydonlarni to'ldiring.",
    continueBtn: "Davom etish",
    mainGreeting: (name) => `Salom, ${name} 👋`,
    mainSubtitle: "Nima bilan shug'ullanamiz?",
    myResultsTitle: "Natijalarim",
    myResultsDesc: "Yechilgan testlar tarixi",
    adminPanelTitle: "Admin panel",
    adminPanelDesc: "Barcha foydalanuvchilar natijalari",
    chooseOperationSubtitle: "Amal turini tanlang",
    chooseLevelSubtitle: "Murakkablik darajasini tanlang",
    chooseDigitsSubtitle: "Sonlar xonasini tanlang",
    chooseTimeSubtitle: (label) => `${label} — har bir savol uchun vaqtni tanlang`,
    finishTestBtn: "🏁 Testni tugatish",
    finishModalTitle: "Testni yakunlaysizmi?",
    finishModalBody: (answered, total) => `Hozirgacha ${answered} / ${total} savolga javob berdingiz. Qolgan savollar hisoblanmaydi.`,
    finishModalCancel: "Davom etish",
    finishModalConfirm: "🏁 Ha, tugatish",
    confirmModalTitle: (choice) => `Javobingiz: ${choice}`,
    confirmModalBody: "Tasdiqlaysizmi yoki qayta o'ylab ko'rasizmi?",
    rethinkBtn: "🔄 Qayta o'ylash",
    confirmBtn: "✅ Tasdiqlash",
    timedOutFeedback: (correct) => `⏰ Vaqt tugadi — javob berolmadingiz. To'g'ri javob: ${correct}`,
    correctFeedback: "✅ To'g'ri!",
    wrongFeedback: (chosen, correct) => `❌ Xato. Siz tanladingiz: ${chosen}. To'g'ri javob: ${correct}`,
    progressLine: (answered, total) => `${answered} / ${total} savol`,
    testFinishedTitle: "Test yakunlandi! 🎉",
    summaryEarly: (total, answered, correct, wrong) => `${total} tadan <b>${answered}</b> tasiga javob berdingiz — shundan <b>${correct}</b> ta to'g'ri, <b>${wrong}</b> ta noto'g'ri`,
    summaryFull: (total, correct, wrong) => `${total} tadan <b>${correct}</b> ta to'g'ri, <b>${wrong}</b> ta noto'g'ri`,
    detailBtn: "Batafsil ko'rish",
    homeBtn: "Bosh menyu",
    noTestsYet: "Hozircha testlar yo'q",
    errorTitle: "Xatolik",
    userTestsTitle: (name) => `${name} testlari`,
    noAnswer: "Javob berilmagan",
    timeoutLine: (correct) => `⏰ Vaqt tugadi — to'g'ri javob: ${correct}`,
    yourAnswerCorrect: (val) => `Javobingiz: ${val} ✔`,
    yourAnswerWrong: (chosen, correct) => `Javobingiz: ${chosen} — to'g'risi: ${correct}`,
    resultSummary: (total, correct, wrong) => `${total} tadan <b>${correct}</b> to'g'ri, <b>${wrong}</b> noto'g'ri`,
    noUsersYet: "Hozircha foydalanuvchilar yo'q",
    noUsername: "username yo'q",
    testsCountSuffix: (n) => `${n} ta test`,
    levelLabel: (d) => `${d}-daraja`,
    digitLabel: (d) => `${d} xonali`,
    operations: {
      add: "Qo'shish", sub: "Ayirish", mul: "Ko'paytirish", div: "Bo'lish", compare: "Solishtirish",
      arith_order: "Amal tartibi", arith_remainder: "Qoldiqli bo'lish", arith_negative: "Manfiy sonlar",
      frac_compare: "Solishtirish", frac_simplify: "Qisqartirish", frac_add: "Qo'shish",
      frac_sub: "Ayirish", frac_mul: "Ko'paytirish", frac_div: "Bo'lish",
      frac_mixed: "Aralash kasr", frac_decimal: "O'nli kasr", frac_basic: "Oddiy kasr",
      percent_of: "Sonning foizini topish", percent_find_whole: "Foiz bo'yicha sonni topish",
      percent_increase: "Narx oshishi", percent_discount: "Chegirma",
      percent_profit_loss: "Foyda/zarar", percent_successive: "Ketma-ket foiz o'zgarishi",
      algebra_equation: "Tenglama", algebra_inequality: "Tengsizlik", algebra_expand: "Qavs ochish",
      algebra_simplify: "Soddalashtirish", algebra_exponent: "Darajalar", algebra_root: "Ildizlar",
      algebra_system: "Sistemalar",
      geo_perimeter: "Perimetr", geo_area: "Yuza", geo_volume: "Hajm", geo_triangle: "Uchburchak",
      geo_quad: "To'rtburchak", geo_circle: "Aylana", geo_pythagoras: "Pifagor teoremasi",
      geo_angles: "Burchaklar",
      func_linear: "Chiziqli funksiya", func_quadratic: "Kvadrat funksiya", func_graph: "Grafik",
      func_value: "Funksiya qiymatini topish", func_zeros: "Nol nuqtalar",
      stat_mean: "O'rtacha qiymat", stat_median: "Mediana", stat_mode: "Moda",
      stat_probability: "Ehtimollik", stat_combinatorics: "Kombinatorika",
      logic_sequence: "Ketma-ketlik", logic_odd_one_out: "Ortiqchasini toping",
      logic_age: "Yosh masalalari", logic_comparison: "Taqqoslash",
    },
    sections: {
      arithmetic: { label: "Arifmetika", desc: "Qo'shish, ayirish, ko'paytirish, bo'lish, solishtirish" },
      fractions: { label: "Kasrlar", desc: "Kasrlar ustida amallar" },
      percent: { label: "Foizlar", desc: "Foizlar bilan bog'liq masalalar" },
      algebra: { label: "Algebra", desc: "Tenglama, tengsizlik, ifodalar bilan ishlash" },
      geometry: { label: "Geometriya", desc: "Perimetr, yuza, hajm va boshqa masalalar" },
      functions: { label: "Funksiyalar", desc: "Chiziqli va kvadrat funksiyalar bilan ishlash" },
      statistics: { label: "Ehtimollik va statistika", desc: "O'rtacha qiymat, mediana, ehtimollik va boshqalar" },
      logic: { label: "Mantiqiy masalalar", desc: "Ketma-ketlik, ortiqchasini topish, yosh va taqqoslash masalalari" },
    },
    sectionCardDesc: {
      fractions: "Kasrlar ustida", percent: "Foizlar ustida",
      algebra: "Algebraik ifodalar ustida", geometry: "Geometrik masalalar ustida",
      functions: "Funksiyalar ustida", statistics: "Ehtimollik va statistika ustida",
      logic: "Mantiqiy fikrlash ustida",
      default: "1–5 xonali sonlar ustida",
    },
    timeOptions: { 30: "30 soniya", 60: "1 daqiqa", 120: "2 daqiqa", 180: "3 daqiqa", 300: "5 daqiqa" },
    instructions: {
      frac_simplify: "Kasrni qisqartiring:",
      frac_mixed: "Aralash songa aylantiring:",
      frac_decimal: "O'nli kasrga aylantiring:",
      logic_sequence: "Ketma-ketlikni davom ettiring:",
      logic_odd_one_out: "Ortiqcha sonni toping:",
    },
    profitLossWords: { profit: "foyda", loss: "zarar" },
    remainderWord: "qoldiq",
    sentences: {
      frac_basic: (q) => `Butun narsa <b>${q.b}</b> ta teng bo'lakka bo'lingan, shundan <b>${q.a}</b> tasi olingan. Bu qanday kasr bilan ifodalanadi?`,
      func_linear: (q) => `y = ${formatLinearExpr(q.a, q.b)} funksiyasida x = ${q.c} bo'lganda, y ning qiymatini toping.`,
      func_quadratic: (q) => `y = ${formatQuadraticExpr(q.a, q.b, q.c)} funksiyasida x = ${q.d} bo'lganda, y ning qiymatini toping.`,
      func_graph: (q) => `y = ${formatLinearExpr(q.a, q.b)} chizig'ining grafigi Y o'qini qaysi nuqtada kesib o'tadi (y qiymati)?`,
      func_value: (q) => (q.d === null || q.d === undefined)
        ? `f(x) = ${formatLinearExpr(q.a, q.b)} bo'lsa, f(${q.c}) ni toping.`
        : `f(x) = ${formatQuadraticExpr(q.a, q.b, q.c)} bo'lsa, f(${q.d}) ni toping.`,
      func_zeros: (q) => `y = ${formatLinearExpr(q.a, q.b)} funksiyasining nol nuqtasini (grafigi X o'qini kesib o'tadigan x qiymatini) toping.`,
      stat_mean: (q) => `Quyidagi sonlarning o'rtacha qiymatini toping: ${q.extra.join(", ")}.`,
      stat_median: (q) => `Quyidagi sonlarning medianasini toping: ${q.extra.join(", ")}.`,
      stat_mode: (q) => `Quyidagi sonlarning modasini (eng ko'p uchraydigan qiymatini) toping: ${q.extra.join(", ")}.`,
      stat_probability: (q) => `Qutida <b>${q.b}</b> ta shar bor, shulardan <b>${q.a}</b> tasi qizil. Tasodifiy tanlangan sharning qizil bo'lish ehtimoli qancha?`,
      stat_combinatorics: (q) => `<b>${q.a}</b> ta kishini qatorga necha xil usul bilan tizish mumkin?`,
      percent_of: (q) => `${q.a} ning <b>${q.b}%</b> i nechiga teng?`,
      percent_find_whole: (q) => `Biror sonning <b>${q.b}%</b> i ${q.a} ga teng. O'sha son nechiga teng?`,
      percent_increase: (q) => `${q.a} so'm bo'lgan narx <b>${q.b}%</b> ga oshdi. Yangi narx nechiga teng?`,
      percent_discount: (q) => `${q.a} so'm bo'lgan mahsulotga <b>${q.b}%</b> chegirma qilindi. Chegirmadagi narx nechiga teng?`,
      percent_profit_loss: (q) => `Tannarxi ${q.a} so'm bo'lgan mahsulot ${q.b} so'mga sotildi. Foyda yoki zarar necha foiz bo'ldi?`,
      percent_successive: (q) => {
        const dir1 = q.b >= 0 ? "oshdi" : "kamaydi";
        const dir2 = q.c >= 0 ? "oshdi" : "kamaydi";
        return `${q.a} dastlab <b>${Math.abs(q.b)}%</b> ga ${dir1}, keyin <b>${Math.abs(q.c)}%</b> ga ${dir2}. Oxirgi qiymat nechiga teng?`;
      },
      geo_perimeter: (q) => `Tomonlari <b>${q.a}</b> va <b>${q.b}</b> bo'lgan to'g'ri to'rtburchakning perimetrini toping.`,
      geo_area: (q) => `Tomonlari <b>${q.a}</b> va <b>${q.b}</b> bo'lgan to'g'ri to'rtburchakning yuzasini toping.`,
      geo_volume: (q) => `O'lchamlari <b>${q.a}</b>, <b>${q.b}</b> va <b>${q.c}</b> bo'lgan to'g'ri burchakli parallelepipedning hajmini toping.`,
      geo_triangle: (q) => `Asosi <b>${q.a}</b> va balandligi <b>${q.b}</b> bo'lgan uchburchakning yuzasini toping.`,
      geo_quad: (q) => `Asoslari <b>${q.a}</b> va <b>${q.b}</b>, balandligi <b>${q.c}</b> bo'lgan trapetsiyaning yuzasini toping.`,
      geo_circle: (q) => q.c === 1
        ? `Radiusi <b>${q.a}</b> bo'lgan aylananing uzunligini toping (π ≈ 3.14).`
        : `Radiusi <b>${q.a}</b> bo'lgan doiraning yuzasini toping (π ≈ 3.14).`,
      geo_pythagoras: (q) => `Katetlari <b>${q.a}</b> va <b>${q.b}</b> bo'lgan to'g'ri burchakli uchburchakning gipotenuzasini toping.`,
      geo_angles: (q) => `Uchburchakning ikkita burchagi <b>${q.a}°</b> va <b>${q.b}°</b> ga teng. Uchinchi burchakni toping.`,
      logic_age: (q) => {
        const diffWord = q.b >= 0 ? "katta" : "kichik";
        const tail = `1-bolaning yoshi hozir <b>${q.a}</b>. 2-bola undan <b>${Math.abs(q.b)}</b> yosh ${diffWord}.`;
        if (q.d === 1) return `${tail} <b>${q.c}</b> yildan keyin ikkalasining yoshlari yig'indisi nechiga teng bo'ladi?`;
        return `${tail} <b>${q.c}</b> yildan keyin 2-bola necha yoshda bo'ladi?`;
      },
      logic_comparison: (q) => {
        const lines = q.extra.join("<br>");
        const question = q.a === 0 ? "Kim (yoki nima) eng katta?" : "Kim (yoki nima) eng kichik?";
        return `${lines}<br><br>${question}`;
      },
    },
    achievements: {
      first_test: { icon: "🎯", label: "Birinchi test" },
      streak_3: { icon: "🔥", label: "3 kunlik seriya" },
      streak_7: { icon: "🔥", label: "7 kunlik seriya" },
      streak_30: { icon: "🔥", label: "30 kunlik seriya" },
      correct_50: { icon: "⭐", label: "50 ta to'g'ri javob" },
      correct_200: { icon: "⭐", label: "200 ta to'g'ri javob" },
      correct_1000: { icon: "🏆", label: "1000 ta to'g'ri javob" },
      perfect_score: { icon: "💯", label: "Mukammal natija (20/20)" },
    },
    statsTitle: "Statistikam",
    statsDesc: "Seriya, yutuqlar va mavzular bo'yicha natijalar",
    streakCardTitle: "🔥 Kunlik seriya",
    streakCurrent: (n) => `Joriy seriya: <b>${n} kun</b>`,
    streakLongest: (n) => `Eng uzun seriya: <b>${n} kun</b>`,
    rankCardTitle: "🏆 Reyting",
    rankLine: (rank, points) => `Siz <b>${rank}-o'rin</b>dasiz (${points} ball)`,
    noRankYet: "Hali reytingga tushmadingiz — birinchi testingizni yakunlang!",
    viewLeaderboardBtn: "To'liq reytingni ko'rish",
    topicStatsTitle: "Mavzular bo'yicha natija",
    noTopicStatsYet: "Hali test yechilmagan",
    achievementsTitle: "Yutuqlar",
    referralCardTitle: "🎁 Do'stni taklif qiling",
    referralDesc: "Havolangiz orqali ro'yxatdan o'tgan har bir do'stingiz shu yerda hisoblanadi.",
    referralCount: (n) => `Taklif qilingan do'stlar: <b>${n}</b>`,
    referralCodeLabel: "Sizning kodingiz:",
    referralNoLink: "Havolani ulashish uchun botga BOT_USERNAME sozlanishi kerak — hozircha kodni ulashing.",
    copyBtn: "📋 Nusxalash",
    copiedMsg: "Nusxalandi!",
    leaderboardTitle: "Reyting",
    leaderboardDesc: "Eng ko'p to'g'ri javob bergan 10 nafar foydalanuvchi",
    noLeaderboardYet: "Hali reytingda hech kim yo'q",
    pointsSuffix: (n) => `${n} ball`,
    adminExportBtn: "📥 Excel formatida yuklab olish",
    recommendedBadge: "✨ Tavsiya",
    newAchievementToast: (label) => `🎉 Yangi yutuq: ${label}!`,
    streakToast: (n) => `🔥 ${n} kunlik seriya!`,
    explanationLabel: "Yechim:",
  },

  ru: {
    genericError: "Произошла ошибка",
    loading: "Загрузка...",
    openInTelegram: "Пожалуйста, откройте бота в Telegram.",
    chooseLanguageTitle: "Выберите язык",
    chooseLanguageSubtitle: "Выберите язык приложения",
    registerTitle: "Регистрация",
    registerSubtitle: "Введите свои данные перед началом тестов",
    firstNameLabel: "Имя",
    firstNamePlaceholder: "Ваше имя",
    lastNameLabel: "Фамилия",
    lastNamePlaceholder: "Ваша фамилия",
    fatherNameLabel: "Отчество",
    fatherNamePlaceholder: "Имя отца",
    dayLabel: "День",
    monthLabel: "Месяц",
    yearLabel: "Год",
    fillAllFields: "Пожалуйста, заполните все поля.",
    continueBtn: "Продолжить",
    mainGreeting: (name) => `Привет, ${name} 👋`,
    mainSubtitle: "Чем займёмся?",
    myResultsTitle: "Мои результаты",
    myResultsDesc: "История пройденных тестов",
    adminPanelTitle: "Панель администратора",
    adminPanelDesc: "Результаты всех пользователей",
    chooseOperationSubtitle: "Выберите тип задания",
    chooseLevelSubtitle: "Выберите уровень сложности",
    chooseDigitsSubtitle: "Выберите разрядность чисел",
    chooseTimeSubtitle: (label) => `${label} — выберите время на каждый вопрос`,
    finishTestBtn: "🏁 Завершить тест",
    finishModalTitle: "Завершить тест?",
    finishModalBody: (answered, total) => `Вы ответили на ${answered} из ${total} вопросов. Оставшиеся вопросы не будут учтены.`,
    finishModalCancel: "Продолжить",
    finishModalConfirm: "🏁 Да, завершить",
    confirmModalTitle: (choice) => `Ваш ответ: ${choice}`,
    confirmModalBody: "Подтверждаете или хотите подумать ещё раз?",
    rethinkBtn: "🔄 Подумать ещё",
    confirmBtn: "✅ Подтвердить",
    timedOutFeedback: (correct) => `⏰ Время вышло — вы не успели ответить. Правильный ответ: ${correct}`,
    correctFeedback: "✅ Правильно!",
    wrongFeedback: (chosen, correct) => `❌ Неверно. Вы выбрали: ${chosen}. Правильный ответ: ${correct}`,
    progressLine: (answered, total) => `${answered} / ${total} вопрос(ов)`,
    testFinishedTitle: "Тест завершён! 🎉",
    summaryEarly: (total, answered, correct, wrong) => `Вы ответили на <b>${answered}</b> из ${total} — из них <b>${correct}</b> верно, <b>${wrong}</b> неверно`,
    summaryFull: (total, correct, wrong) => `Из ${total}: <b>${correct}</b> верно, <b>${wrong}</b> неверно`,
    detailBtn: "Подробнее",
    homeBtn: "Главное меню",
    noTestsYet: "Пока нет тестов",
    errorTitle: "Ошибка",
    userTestsTitle: (name) => `Тесты пользователя ${name}`,
    noAnswer: "Нет ответа",
    timeoutLine: (correct) => `⏰ Время вышло — правильный ответ: ${correct}`,
    yourAnswerCorrect: (val) => `Ваш ответ: ${val} ✔`,
    yourAnswerWrong: (chosen, correct) => `Ваш ответ: ${chosen} — правильно: ${correct}`,
    resultSummary: (total, correct, wrong) => `Из ${total}: <b>${correct}</b> верно, <b>${wrong}</b> неверно`,
    noUsersYet: "Пока нет пользователей",
    noUsername: "нет username",
    testsCountSuffix: (n) => `тестов: ${n}`,
    levelLabel: (d) => `${d}-уровень`,
    digitLabel: (d) => `${d}-значные`,
    operations: {
      add: "Сложение", sub: "Вычитание", mul: "Умножение", div: "Деление", compare: "Сравнение",
      arith_order: "Порядок действий", arith_remainder: "Деление с остатком", arith_negative: "Отрицательные числа",
      frac_compare: "Сравнение", frac_simplify: "Сокращение", frac_add: "Сложение",
      frac_sub: "Вычитание", frac_mul: "Умножение", frac_div: "Деление",
      frac_mixed: "Смешанная дробь", frac_decimal: "Десятичная дробь", frac_basic: "Обычная дробь",
      percent_of: "Процент от числа", percent_find_whole: "Число по проценту",
      percent_increase: "Повышение цены", percent_discount: "Скидка",
      percent_profit_loss: "Прибыль/убыток", percent_successive: "Последовательное изменение процента",
      algebra_equation: "Уравнение", algebra_inequality: "Неравенство", algebra_expand: "Раскрытие скобок",
      algebra_simplify: "Упрощение", algebra_exponent: "Степени", algebra_root: "Корни",
      algebra_system: "Системы уравнений",
      geo_perimeter: "Периметр", geo_area: "Площадь", geo_volume: "Объём", geo_triangle: "Треугольник",
      geo_quad: "Четырёхугольник", geo_circle: "Окружность", geo_pythagoras: "Теорема Пифагора",
      geo_angles: "Углы",
      func_linear: "Линейная функция", func_quadratic: "Квадратичная функция", func_graph: "График",
      func_value: "Нахождение значения функции", func_zeros: "Нули функции",
      stat_mean: "Среднее значение", stat_median: "Медиана", stat_mode: "Мода",
      stat_probability: "Вероятность", stat_combinatorics: "Комбинаторика",
      logic_sequence: "Последовательность", logic_odd_one_out: "Найди лишнее",
      logic_age: "Задачи на возраст", logic_comparison: "Сравнение",
    },
    sections: {
      arithmetic: { label: "Арифметика", desc: "Сложение, вычитание, умножение, деление, сравнение" },
      fractions: { label: "Дроби", desc: "Действия с дробями" },
      percent: { label: "Проценты", desc: "Задачи на проценты" },
      algebra: { label: "Алгебра", desc: "Уравнения, неравенства, работа с выражениями" },
      geometry: { label: "Геометрия", desc: "Периметр, площадь, объём и другие задачи" },
      functions: { label: "Функции", desc: "Работа с линейными и квадратичными функциями" },
      statistics: { label: "Вероятность и статистика", desc: "Среднее значение, медиана, вероятность и другое" },
      logic: { label: "Логические задачи", desc: "Последовательности, лишнее число, задачи на возраст и сравнение" },
    },
    sectionCardDesc: {
      fractions: "Действия с дробями", percent: "Задачи на проценты",
      algebra: "Алгебраические выражения", geometry: "Геометрические задачи",
      functions: "Работа с функциями", statistics: "Вероятность и статистика",
      logic: "Логическое мышление",
      default: "Числа от 1 до 5 разрядов",
    },
    timeOptions: { 30: "30 секунд", 60: "1 минута", 120: "2 минуты", 180: "3 минуты", 300: "5 минут" },
    instructions: {
      frac_simplify: "Сократите дробь:",
      frac_mixed: "Преобразуйте в смешанное число:",
      frac_decimal: "Преобразуйте в десятичную дробь:",
      logic_sequence: "Продолжите последовательность:",
      logic_odd_one_out: "Найдите лишнее число:",
    },
    profitLossWords: { profit: "прибыль", loss: "убыток" },
    remainderWord: "остаток",
    sentences: {
      frac_basic: (q) => `Целое разделено на <b>${q.b}</b> равных частей, из них взято <b>${q.a}</b>. Какой дробью это выражается?`,
      func_linear: (q) => `При y = ${formatLinearExpr(q.a, q.b)}, найдите значение y при x = ${q.c}.`,
      func_quadratic: (q) => `При y = ${formatQuadraticExpr(q.a, q.b, q.c)}, найдите значение y при x = ${q.d}.`,
      func_graph: (q) => `В какой точке график линии y = ${formatLinearExpr(q.a, q.b)} пересекает ось Y (значение y)?`,
      func_value: (q) => (q.d === null || q.d === undefined)
        ? `Если f(x) = ${formatLinearExpr(q.a, q.b)}, найдите f(${q.c}).`
        : `Если f(x) = ${formatQuadraticExpr(q.a, q.b, q.c)}, найдите f(${q.d}).`,
      func_zeros: (q) => `Найдите нуль функции y = ${formatLinearExpr(q.a, q.b)} (значение x, при котором график пересекает ось X).`,
      stat_mean: (q) => `Найдите среднее значение следующих чисел: ${q.extra.join(", ")}.`,
      stat_median: (q) => `Найдите медиану следующих чисел: ${q.extra.join(", ")}.`,
      stat_mode: (q) => `Найдите моду (наиболее часто встречающееся значение) следующих чисел: ${q.extra.join(", ")}.`,
      stat_probability: (q) => `В коробке <b>${q.b}</b> шаров, из них <b>${q.a}</b> красных. Какова вероятность вытащить красный шар наугад?`,
      stat_combinatorics: (q) => `Сколькими способами можно выстроить в ряд <b>${q.a}</b> человек?`,
      percent_of: (q) => `Чему равно <b>${q.b}%</b> от ${q.a}?`,
      percent_find_whole: (q) => `<b>${q.b}%</b> некоторого числа равны ${q.a}. Чему равно это число?`,
      percent_increase: (q) => `Цена ${q.a} сум выросла на <b>${q.b}%</b>. Чему равна новая цена?`,
      percent_discount: (q) => `На товар стоимостью ${q.a} сум сделали скидку <b>${q.b}%</b>. Чему равна цена со скидкой?`,
      percent_profit_loss: (q) => `Товар себестоимостью ${q.a} сум продали за ${q.b} сум. Сколько процентов составила прибыль или убыток?`,
      percent_successive: (q) => {
        const dir1 = q.b >= 0 ? "увеличилось" : "уменьшилось";
        const dir2 = q.c >= 0 ? "увеличилось" : "уменьшилось";
        return `Значение ${q.a} сначала <b>${dir1}</b> на ${Math.abs(q.b)}%, затем <b>${dir2}</b> на ${Math.abs(q.c)}%. Чему равно итоговое значение?`;
      },
      geo_perimeter: (q) => `Найдите периметр прямоугольника со сторонами <b>${q.a}</b> и <b>${q.b}</b>.`,
      geo_area: (q) => `Найдите площадь прямоугольника со сторонами <b>${q.a}</b> и <b>${q.b}</b>.`,
      geo_volume: (q) => `Найдите объём прямоугольного параллелепипеда с измерениями <b>${q.a}</b>, <b>${q.b}</b> и <b>${q.c}</b>.`,
      geo_triangle: (q) => `Найдите площадь треугольника с основанием <b>${q.a}</b> и высотой <b>${q.b}</b>.`,
      geo_quad: (q) => `Найдите площадь трапеции с основаниями <b>${q.a}</b> и <b>${q.b}</b> и высотой <b>${q.c}</b>.`,
      geo_circle: (q) => q.c === 1
        ? `Найдите длину окружности радиусом <b>${q.a}</b> (π ≈ 3.14).`
        : `Найдите площадь круга радиусом <b>${q.a}</b> (π ≈ 3.14).`,
      geo_pythagoras: (q) => `Найдите гипотенузу прямоугольного треугольника с катетами <b>${q.a}</b> и <b>${q.b}</b>.`,
      geo_angles: (q) => `Два угла треугольника равны <b>${q.a}°</b> и <b>${q.b}°</b>. Найдите третий угол.`,
      logic_age: (q) => {
        const diffWord = q.b >= 0 ? "старше" : "младше";
        const tail = `Возраст первого ребёнка сейчас <b>${q.a}</b>. Второй ребёнок на <b>${Math.abs(q.b)}</b> лет ${diffWord}.`;
        if (q.d === 1) return `${tail} Через <b>${q.c}</b> лет чему будет равна сумма их возрастов?`;
        return `${tail} Через <b>${q.c}</b> лет сколько лет будет второму ребёнку?`;
      },
      logic_comparison: (q) => {
        const lines = q.extra.join("<br>");
        const question = q.a === 0 ? "Кто (или что) самый большой?" : "Кто (или что) самый маленький?";
        return `${lines}<br><br>${question}`;
      },
    },
    achievements: {
      first_test: { icon: "🎯", label: "Первый тест" },
      streak_3: { icon: "🔥", label: "Серия 3 дня" },
      streak_7: { icon: "🔥", label: "Серия 7 дней" },
      streak_30: { icon: "🔥", label: "Серия 30 дней" },
      correct_50: { icon: "⭐", label: "50 верных ответов" },
      correct_200: { icon: "⭐", label: "200 верных ответов" },
      correct_1000: { icon: "🏆", label: "1000 верных ответов" },
      perfect_score: { icon: "💯", label: "Идеальный результат (20/20)" },
    },
    statsTitle: "Моя статистика",
    statsDesc: "Серия, достижения и результаты по темам",
    streakCardTitle: "🔥 Ежедневная серия",
    streakCurrent: (n) => `Текущая серия: <b>${n} дн.</b>`,
    streakLongest: (n) => `Самая длинная серия: <b>${n} дн.</b>`,
    rankCardTitle: "🏆 Рейтинг",
    rankLine: (rank, points) => `Вы на <b>${rank}-м месте</b> (${points} баллов)`,
    noRankYet: "Вы ещё не в рейтинге — завершите свой первый тест!",
    viewLeaderboardBtn: "Смотреть весь рейтинг",
    topicStatsTitle: "Результаты по темам",
    noTopicStatsYet: "Тестов пока не было",
    achievementsTitle: "Достижения",
    referralCardTitle: "🎁 Пригласите друга",
    referralDesc: "Каждый друг, зарегистрировавшийся по вашей ссылке, учитывается здесь.",
    referralCount: (n) => `Приглашено друзей: <b>${n}</b>`,
    referralCodeLabel: "Ваш код:",
    referralNoLink: "Для ссылки нужно настроить BOT_USERNAME у бота — пока поделитесь кодом.",
    copyBtn: "📋 Копировать",
    copiedMsg: "Скопировано!",
    leaderboardTitle: "Рейтинг",
    leaderboardDesc: "10 пользователей с наибольшим числом верных ответов",
    noLeaderboardYet: "В рейтинге пока никого нет",
    pointsSuffix: (n) => `${n} баллов`,
    adminExportBtn: "📥 Скачать в Excel",
    recommendedBadge: "✨ Рекомендуем",
    newAchievementToast: (label) => `🎉 Новое достижение: ${label}!`,
    streakToast: (n) => `🔥 Серия ${n} дней!`,
    explanationLabel: "Решение:",
  },

  en: {
    genericError: "Something went wrong",
    loading: "Loading...",
    openInTelegram: "Please open the bot inside Telegram.",
    chooseLanguageTitle: "Choose language",
    chooseLanguageSubtitle: "Choose the app language",
    registerTitle: "Registration",
    registerSubtitle: "Enter your details before starting the tests",
    firstNameLabel: "First name",
    firstNamePlaceholder: "Your first name",
    lastNameLabel: "Last name",
    lastNamePlaceholder: "Your last name",
    fatherNameLabel: "Father's name",
    fatherNamePlaceholder: "Your father's name",
    dayLabel: "Day",
    monthLabel: "Month",
    yearLabel: "Year",
    fillAllFields: "Please fill in all the fields.",
    continueBtn: "Continue",
    mainGreeting: (name) => `Hi, ${name} 👋`,
    mainSubtitle: "What shall we work on?",
    myResultsTitle: "My results",
    myResultsDesc: "History of completed tests",
    adminPanelTitle: "Admin panel",
    adminPanelDesc: "Results of all users",
    chooseOperationSubtitle: "Choose a topic",
    chooseLevelSubtitle: "Choose the difficulty level",
    chooseDigitsSubtitle: "Choose the number of digits",
    chooseTimeSubtitle: (label) => `${label} — choose the time per question`,
    finishTestBtn: "🏁 Finish test",
    finishModalTitle: "Finish the test?",
    finishModalBody: (answered, total) => `So far you've answered ${answered} of ${total} questions. Remaining questions won't be counted.`,
    finishModalCancel: "Keep going",
    finishModalConfirm: "🏁 Yes, finish",
    confirmModalTitle: (choice) => `Your answer: ${choice}`,
    confirmModalBody: "Confirm your answer, or think again?",
    rethinkBtn: "🔄 Think again",
    confirmBtn: "✅ Confirm",
    timedOutFeedback: (correct) => `⏰ Time's up — you didn't answer in time. Correct answer: ${correct}`,
    correctFeedback: "✅ Correct!",
    wrongFeedback: (chosen, correct) => `❌ Wrong. You chose: ${chosen}. Correct answer: ${correct}`,
    progressLine: (answered, total) => `${answered} / ${total} questions`,
    testFinishedTitle: "Test finished! 🎉",
    summaryEarly: (total, answered, correct, wrong) => `You answered <b>${answered}</b> of ${total} — <b>${correct}</b> correct, <b>${wrong}</b> wrong`,
    summaryFull: (total, correct, wrong) => `Out of ${total}: <b>${correct}</b> correct, <b>${wrong}</b> wrong`,
    detailBtn: "View details",
    homeBtn: "Main menu",
    noTestsYet: "No tests yet",
    errorTitle: "Error",
    userTestsTitle: (name) => `${name}'s tests`,
    noAnswer: "No answer given",
    timeoutLine: (correct) => `⏰ Time's up — correct answer: ${correct}`,
    yourAnswerCorrect: (val) => `Your answer: ${val} ✔`,
    yourAnswerWrong: (chosen, correct) => `Your answer: ${chosen} — correct: ${correct}`,
    resultSummary: (total, correct, wrong) => `Out of ${total}: <b>${correct}</b> correct, <b>${wrong}</b> wrong`,
    noUsersYet: "No users yet",
    noUsername: "no username",
    testsCountSuffix: (n) => `${n} test(s)`,
    levelLabel: (d) => `Level ${d}`,
    digitLabel: (d) => `${d} digits`,
    operations: {
      add: "Addition", sub: "Subtraction", mul: "Multiplication", div: "Division", compare: "Comparison",
      arith_order: "Order of operations", arith_remainder: "Division with remainder", arith_negative: "Negative numbers",
      frac_compare: "Comparison", frac_simplify: "Simplifying", frac_add: "Addition",
      frac_sub: "Subtraction", frac_mul: "Multiplication", frac_div: "Division",
      frac_mixed: "Mixed number", frac_decimal: "Decimal", frac_basic: "Basic fraction",
      percent_of: "Percentage of a number", percent_find_whole: "Find the whole from a percent",
      percent_increase: "Price increase", percent_discount: "Discount",
      percent_profit_loss: "Profit/loss", percent_successive: "Successive percent change",
      algebra_equation: "Equation", algebra_inequality: "Inequality", algebra_expand: "Expanding brackets",
      algebra_simplify: "Simplifying", algebra_exponent: "Exponents", algebra_root: "Roots",
      algebra_system: "Systems of equations",
      geo_perimeter: "Perimeter", geo_area: "Area", geo_volume: "Volume", geo_triangle: "Triangle",
      geo_quad: "Quadrilateral", geo_circle: "Circle", geo_pythagoras: "Pythagorean theorem",
      geo_angles: "Angles",
      func_linear: "Linear function", func_quadratic: "Quadratic function", func_graph: "Graph",
      func_value: "Finding a function's value", func_zeros: "Zeros of a function",
      stat_mean: "Mean", stat_median: "Median", stat_mode: "Mode",
      stat_probability: "Probability", stat_combinatorics: "Combinatorics",
      logic_sequence: "Sequence", logic_odd_one_out: "Find the odd one out",
      logic_age: "Age problems", logic_comparison: "Comparison",
    },
    sections: {
      arithmetic: { label: "Arithmetic", desc: "Addition, subtraction, multiplication, division, comparison" },
      fractions: { label: "Fractions", desc: "Operations with fractions" },
      percent: { label: "Percentages", desc: "Percent-related problems" },
      algebra: { label: "Algebra", desc: "Equations, inequalities, working with expressions" },
      geometry: { label: "Geometry", desc: "Perimeter, area, volume and other problems" },
      functions: { label: "Functions", desc: "Working with linear and quadratic functions" },
      statistics: { label: "Probability & Statistics", desc: "Mean, median, probability and more" },
      logic: { label: "Logic problems", desc: "Sequences, odd one out, age and comparison problems" },
    },
    sectionCardDesc: {
      fractions: "Working with fractions", percent: "Working with percentages",
      algebra: "Algebraic expressions", geometry: "Geometry problems",
      functions: "Working with functions", statistics: "Probability and statistics",
      logic: "Logical thinking",
      default: "1–5 digit numbers",
    },
    timeOptions: { 30: "30 seconds", 60: "1 minute", 120: "2 minutes", 180: "3 minutes", 300: "5 minutes" },
    instructions: {
      frac_simplify: "Simplify the fraction:",
      frac_mixed: "Convert to a mixed number:",
      frac_decimal: "Convert to a decimal:",
      logic_sequence: "Continue the sequence:",
      logic_odd_one_out: "Find the odd one out:",
    },
    profitLossWords: { profit: "profit", loss: "loss" },
    remainderWord: "remainder",
    sentences: {
      frac_basic: (q) => `A whole is divided into <b>${q.b}</b> equal parts, and <b>${q.a}</b> of them are taken. What fraction represents this?`,
      func_linear: (q) => `For y = ${formatLinearExpr(q.a, q.b)}, find the value of y when x = ${q.c}.`,
      func_quadratic: (q) => `For y = ${formatQuadraticExpr(q.a, q.b, q.c)}, find the value of y when x = ${q.d}.`,
      func_graph: (q) => `At what point does the line y = ${formatLinearExpr(q.a, q.b)} cross the Y-axis (the y-value)?`,
      func_value: (q) => (q.d === null || q.d === undefined)
        ? `If f(x) = ${formatLinearExpr(q.a, q.b)}, find f(${q.c}).`
        : `If f(x) = ${formatQuadraticExpr(q.a, q.b, q.c)}, find f(${q.d}).`,
      func_zeros: (q) => `Find the zero of the function y = ${formatLinearExpr(q.a, q.b)} (the x-value where the graph crosses the X-axis).`,
      stat_mean: (q) => `Find the mean of the following numbers: ${q.extra.join(", ")}.`,
      stat_median: (q) => `Find the median of the following numbers: ${q.extra.join(", ")}.`,
      stat_mode: (q) => `Find the mode (most frequent value) of the following numbers: ${q.extra.join(", ")}.`,
      stat_probability: (q) => `A box has <b>${q.b}</b> balls, <b>${q.a}</b> of which are red. What is the probability of picking a red ball at random?`,
      stat_combinatorics: (q) => `In how many ways can <b>${q.a}</b> people be arranged in a row?`,
      percent_of: (q) => `What is <b>${q.b}%</b> of ${q.a}?`,
      percent_find_whole: (q) => `<b>${q.b}%</b> of a number is ${q.a}. What is that number?`,
      percent_increase: (q) => `A price of ${q.a} increased by <b>${q.b}%</b>. What is the new price?`,
      percent_discount: (q) => `An item priced at ${q.a} got a <b>${q.b}%</b> discount. What is the discounted price?`,
      percent_profit_loss: (q) => `An item costing ${q.a} was sold for ${q.b}. What percent profit or loss was made?`,
      percent_successive: (q) => {
        const dir1 = q.b >= 0 ? "increased" : "decreased";
        const dir2 = q.c >= 0 ? "increased" : "decreased";
        return `${q.a} first <b>${dir1}</b> by ${Math.abs(q.b)}%, then <b>${dir2}</b> by ${Math.abs(q.c)}%. What is the final value?`;
      },
      geo_perimeter: (q) => `Find the perimeter of a rectangle with sides <b>${q.a}</b> and <b>${q.b}</b>.`,
      geo_area: (q) => `Find the area of a rectangle with sides <b>${q.a}</b> and <b>${q.b}</b>.`,
      geo_volume: (q) => `Find the volume of a rectangular prism with dimensions <b>${q.a}</b>, <b>${q.b}</b> and <b>${q.c}</b>.`,
      geo_triangle: (q) => `Find the area of a triangle with base <b>${q.a}</b> and height <b>${q.b}</b>.`,
      geo_quad: (q) => `Find the area of a trapezoid with bases <b>${q.a}</b> and <b>${q.b}</b> and height <b>${q.c}</b>.`,
      geo_circle: (q) => q.c === 1
        ? `Find the circumference of a circle with radius <b>${q.a}</b> (π ≈ 3.14).`
        : `Find the area of a circle with radius <b>${q.a}</b> (π ≈ 3.14).`,
      geo_pythagoras: (q) => `Find the hypotenuse of a right triangle with legs <b>${q.a}</b> and <b>${q.b}</b>.`,
      geo_angles: (q) => `Two angles of a triangle are <b>${q.a}°</b> and <b>${q.b}°</b>. Find the third angle.`,
      logic_age: (q) => {
        const diffWord = q.b >= 0 ? "older" : "younger";
        const tail = `The first child is currently <b>${q.a}</b> years old. The second child is <b>${Math.abs(q.b)}</b> years ${diffWord}.`;
        if (q.d === 1) return `${tail} In <b>${q.c}</b> years, what will the sum of their ages be?`;
        return `${tail} In <b>${q.c}</b> years, how old will the second child be?`;
      },
      logic_comparison: (q) => {
        const lines = q.extra.join("<br>");
        const question = q.a === 0 ? "Who (or what) is the biggest?" : "Who (or what) is the smallest?";
        return `${lines}<br><br>${question}`;
      },
    },
    achievements: {
      first_test: { icon: "🎯", label: "First test" },
      streak_3: { icon: "🔥", label: "3-day streak" },
      streak_7: { icon: "🔥", label: "7-day streak" },
      streak_30: { icon: "🔥", label: "30-day streak" },
      correct_50: { icon: "⭐", label: "50 correct answers" },
      correct_200: { icon: "⭐", label: "200 correct answers" },
      correct_1000: { icon: "🏆", label: "1000 correct answers" },
      perfect_score: { icon: "💯", label: "Perfect score (20/20)" },
    },
    statsTitle: "My stats",
    statsDesc: "Streak, achievements and results by topic",
    streakCardTitle: "🔥 Daily streak",
    streakCurrent: (n) => `Current streak: <b>${n} days</b>`,
    streakLongest: (n) => `Longest streak: <b>${n} days</b>`,
    rankCardTitle: "🏆 Leaderboard",
    rankLine: (rank, points) => `You're in <b>#${rank}</b> place (${points} points)`,
    noRankYet: "You're not ranked yet — finish your first test!",
    viewLeaderboardBtn: "View full leaderboard",
    topicStatsTitle: "Results by topic",
    noTopicStatsYet: "No tests taken yet",
    achievementsTitle: "Achievements",
    referralCardTitle: "🎁 Invite a friend",
    referralDesc: "Every friend who registers through your link is counted here.",
    referralCount: (n) => `Friends invited: <b>${n}</b>`,
    referralCodeLabel: "Your code:",
    referralNoLink: "A shareable link needs BOT_USERNAME configured on the bot — share the code for now.",
    copyBtn: "📋 Copy",
    copiedMsg: "Copied!",
    leaderboardTitle: "Leaderboard",
    leaderboardDesc: "Top 10 users by correct answers",
    noLeaderboardYet: "No one is on the leaderboard yet",
    pointsSuffix: (n) => `${n} points`,
    adminExportBtn: "📥 Download as Excel",
    recommendedBadge: "✨ Recommended",
    newAchievementToast: (label) => `🎉 New achievement: ${label}!`,
    streakToast: (n) => `🔥 ${n}-day streak!`,
    explanationLabel: "Solution:",
  },
};

function t(key, ...args) {
  const dict = I18N[LANG] || I18N.uz;
  const entry = dict[key] !== undefined ? dict[key] : I18N.uz[key];
  if (typeof entry === "function") {
    // Ba'zi joylarda t("key")(arg1, arg2) ko'rinishida chaqiriladi (funksiyani
    // qaytarib, keyin darhol chaqiradi), ba'zilarida esa t("key", arg1) — ikkalasi
    // ham ishlashi uchun: argument berilmagan bo'lsa funksiyaning o'zini qaytaramiz.
    return args.length > 0 ? entry(...args) : entry;
  }
  return entry;
}

function opLabel(key) {
  const dict = I18N[LANG] || I18N.uz;
  return (dict.operations && dict.operations[key])
    || (CONFIG && CONFIG.operations[key] && CONFIG.operations[key].label)
    || key;
}

function sectionLabel(key) {
  const dict = I18N[LANG] || I18N.uz;
  return (dict.sections[key] && dict.sections[key].label) || key;
}

function sectionDescText(key) {
  const dict = I18N[LANG] || I18N.uz;
  return (dict.sections[key] && dict.sections[key].desc) || "";
}

function sectionCardDesc(key) {
  const dict = I18N[LANG] || I18N.uz;
  return dict.sectionCardDesc[key] || dict.sectionCardDesc.default;
}

function timeLabel(seconds) {
  const dict = I18N[LANG] || I18N.uz;
  return (dict.timeOptions && dict.timeOptions[seconds]) || `${seconds}s`;
}

function instructionFor(op) {
  const dict = I18N[LANG] || I18N.uz;
  return dict.instructions[op];
}

function translateChoiceLabel(op, raw) {
  if (op === "percent_profit_loss" && typeof raw === "string") {
    const words = (I18N[LANG] || I18N.uz).profitLossWords;
    return raw.replace("foyda", words.profit).replace("zarar", words.loss);
  }
  if (op === "arith_remainder" && typeof raw === "string") {
    const word = (I18N[LANG] || I18N.uz).remainderWord;
    return raw.replace("qoldiq", word);
  }
  return raw;
}

function loadStoredLanguage() {
  try {
    return localStorage.getItem(LANG_STORAGE_KEY);
  } catch (e) {
    return null;
  }
}

function storeLanguage(lang) {
  try {
    localStorage.setItem(LANG_STORAGE_KEY, lang);
  } catch (e) {}
}

async function setLanguage(newLang) {
  LANG = newLang;
  storeLanguage(LANG);
  document.documentElement.lang = LANG;
  if (ME && ME.registered) {
    try {
      await api("/api/language", { method: "POST", body: { language: LANG } });
    } catch (e) {}
  }
  render();
}

function showLanguageModal() {
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "lang-modal";
  modal.innerHTML = `
    <div class="modal-sheet">
      <h3>${t("chooseLanguageTitle")}</h3>
      <div class="lang-options">
        ${LANGS.map((code) => `
          <button class="lang-option-btn${code === LANG ? " active" : ""}" data-lang="${code}">
            <span class="flag">${LANG_META[code].flag}</span> ${LANG_META[code].name}
          </button>
        `).join("")}
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.remove();
  });
  modal.querySelectorAll(".lang-option-btn").forEach((btn) => {
    btn.onclick = async () => {
      const newLang = btn.dataset.lang;
      modal.remove();
      await setLanguage(newLang);
    };
  });
}

let CONFIG = null;
let ME = null; // {telegram_id, registered, profile, is_admin}

const state = {
  screen: "loading",
  selection: { section: null, operation: null, digits: null, timePerQuestion: null },
  test: null, // {attempt_id, total_questions, time_per_question, question, progress}
  timer: { deadline: 0, raf: null, total: 0 },
  pendingChoice: null, // tanlangan-lekin-hali-tasdiqlanmagan javob
  lastFeedback: null, // {isCorrect, correctAnswer, chosen, timedOut, operation}
  viewAttemptId: null,
  viewUserId: null,
  navStack: [],
};

function pushScreen(screen, extra) {
  state.navStack.push({ screen: state.screen, selection: { ...state.selection } });
  Object.assign(state, extra || {});
  state.screen = screen;
  render();
}

function goBack() {
  const prev = state.navStack.pop();
  if (!prev) {
    state.screen = "main";
  } else {
    state.screen = prev.screen;
    state.selection = prev.selection;
  }
  render();
}

// ---------- API helper ----------
async function api(path, options = {}) {
  const res = await fetch(path, {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": INIT_DATA,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    let msg = t("genericError");
    try {
      const j = await res.json();
      msg = j.detail || msg;
    } catch (e) {}
    throw new Error(msg);
  }
  return res.json();
}

// ---------- Bootstrap ----------
async function init() {
  try {
    CONFIG = await api("/api/config");
    ME = await api("/api/me");

    if (ME.registered && ME.profile && ME.profile.language && LANGS.includes(ME.profile.language)) {
      LANG = ME.profile.language;
      storeLanguage(LANG);
      state.screen = "main";
    } else {
      const stored = loadStoredLanguage();
      if (stored && LANGS.includes(stored)) {
        LANG = stored;
        state.screen = ME.registered ? "main" : "register";
      } else {
        state.screen = "language";
      }
    }
    document.documentElement.lang = LANG;
  } catch (e) {
    appEl.innerHTML = `<div class="empty-state">${escapeHtml(t("genericError"))}: ${escapeHtml(e.message)}<br/>${escapeHtml(t("openInTelegram"))}</div>`;
    return;
  }
  render();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function dash(v) {
  return v === null || v === undefined ? "—" : escapeHtml(String(v));
}

// ---------- Kasr ko'rinishi (numerator ustida, denominator ostida) ----------
function fracHtml(n, d) {
  return `<span class="frac"><span class="num">${dash(n)}</span><span class="den">${dash(d)}</span></span>`;
}

// ---------- Savol ifodasi (test ekrani va natija tafsiloti uchun umumiy) ----------
function questionExprHtml(q) {
  if (q.display_text) {
    return escapeHtml(q.display_text).replace(/\n/g, "<br>");
  }
  const dict = I18N[LANG] || I18N.uz;
  const sentenceFn = dict.sentences[q.operation];
  if (sentenceFn) return sentenceFn(q);
  switch (q.operation) {
    case "add": case "sub": case "mul": case "div": case "arith_remainder": {
      const symbol = CONFIG.operations[q.operation].symbol;
      return `${q.a} <span class="op-symbol">${symbol}</span> ${q.b}`;
    }
    case "compare":
      return `${q.a} <span class="op-symbol">⚖</span> ${q.b}`;
    case "frac_compare":
      return `${fracHtml(q.a, q.b)} <span class="op-symbol">⚖</span> ${fracHtml(q.c, q.d)}`;
    case "frac_add": case "frac_sub": case "frac_mul": case "frac_div": {
      const symbol = CONFIG.operations[q.operation].symbol;
      return `${fracHtml(q.a, q.b)} <span class="op-symbol">${symbol}</span> ${fracHtml(q.c, q.d)}`;
    }
    case "frac_simplify": case "frac_mixed": case "frac_decimal":
      return fracHtml(q.a, q.b);
    case "algebra_exponent":
      return `${q.a}${superscript(q.b)}`;
    case "algebra_root":
      return `${q.b === 3 ? "∛" : "√"}${q.a}`;
    default:
      return `${q.a} ? ${q.b}`;
  }
}

function questionSuffix(q) {
  if (q.display_text) return "";
  return NO_SUFFIX_OPS.has(q.operation) ? "" : " = ?";
}

// ---------- Xato/to'g'ri javobdan keyin ko'rsatiladigan qisqa yechim
// (til-neytral — faqat sonlar va matematik belgilardan iborat) ----------
const EXPLANATIONS = {
  arith_remainder: (q, ans) => {
    const parts = String(ans).split(" ");
    return `${q.a} = ${parts[0]} × ${q.b} + ${parts[2]}`;
  },
  percent_of: (q, ans) => `${q.a} × ${q.b} ÷ 100 = ${ans}`,
  percent_find_whole: (q, ans) => `${q.a} ÷ ${q.b} × 100 = ${ans}`,
  percent_increase: (q, ans) => `${q.a} + (${q.a} × ${q.b} ÷ 100) = ${ans}`,
  percent_discount: (q, ans) => `${q.a} − (${q.a} × ${q.b} ÷ 100) = ${ans}`,
  percent_profit_loss: (q, ans) => `(${q.b} − ${q.a}) ÷ ${q.a} × 100% = ${translateChoiceLabel("percent_profit_loss", ans)}`,
  percent_successive: (q, ans) => `${q.a} → ×(100${q.b >= 0 ? "+" : ""}${q.b})/100 → ×(100${q.c >= 0 ? "+" : ""}${q.c})/100 = ${ans}`,
  algebra_exponent: (q, ans) => `${q.a}${superscript(q.b)} = ${Array(q.b).fill(q.a).join(" × ")} = ${ans}`,
  algebra_root: (q, ans) => `${ans}${superscript(q.b)} = ${q.a}`,
  geo_perimeter: (q, ans) => `P = 2×(${q.a}+${q.b}) = ${ans}`,
  geo_area: (q, ans) => `S = ${q.a}×${q.b} = ${ans}`,
  geo_volume: (q, ans) => `V = ${q.a}×${q.b}×${q.c} = ${ans}`,
  geo_triangle: (q, ans) => `S = (${q.a}×${q.b})÷2 = ${ans}`,
  geo_quad: (q, ans) => `S = ((${q.a}+${q.b})×${q.c})÷2 = ${ans}`,
  geo_circle: (q, ans) => q.c === 1 ? `L = 2×π×${q.a} ≈ ${ans}` : `S = π×${q.a}² ≈ ${ans}`,
  geo_pythagoras: (q, ans) => `c = √(${q.a}² + ${q.b}²) = ${ans}`,
  geo_angles: (q, ans) => `180° − ${q.a}° − ${q.b}° = ${ans}`,
  func_linear: (q, ans) => `${q.a}×(${q.c}) + (${q.b}) = ${ans}`,
  func_quadratic: (q, ans) => `${q.a}×(${q.d})² + ${q.b}×(${q.d}) + (${q.c}) = ${ans}`,
  func_graph: (q, ans) => `x=0 → y = ${ans}`,
  func_value: (q, ans) => (q.d === null || q.d === undefined)
    ? `${q.a}×(${q.c}) + (${q.b}) = ${ans}`
    : `${q.a}×(${q.d})² + ${q.b}×(${q.d}) + (${q.c}) = ${ans}`,
  func_zeros: (q, ans) => `${q.a}x + ${q.b} = 0 → x = ${ans}`,
  stat_mean: (q, ans) => `(${q.extra.join(" + ")}) ÷ ${q.extra.length} = ${ans}`,
  stat_median: (q, ans) => `${[...q.extra].sort((x, y) => x - y).join(", ")} → Me = ${ans}`,
  stat_mode: (q, ans) => `Mo = ${ans}`,
  stat_probability: (q, ans) => `${q.a}/${q.b} = ${ans}`,
  stat_combinatorics: (q, ans) => `${q.a}! = ${Array.from({ length: q.a }, (_, i) => i + 1).join("×")} = ${ans}`,
  logic_sequence: (q, ans) => `${(q.display_text || "").replace(/,\s*\?$/, "")}, ${ans}`,
  logic_age: (q, ans) => (q.d === 1)
    ? `(${q.a}+${q.c}) + (${q.a}${q.b >= 0 ? "+" : ""}${q.b}+${q.c}) = ${ans}`
    : `${q.a}${q.b >= 0 ? "+" : ""}${q.b}+${q.c} = ${ans}`,
};

// ---------- Render dispatch ----------
function render() {
  switch (state.screen) {
    case "language": return renderLanguageSelect();
    case "register": return renderRegister();
    case "main": return renderMain();
    case "section": return renderSection();
    case "digits": return renderDigits();
    case "time": return renderTime();
    case "test": return renderTest();
    case "test_result": return renderTestResult();
    case "my_results": return renderResultsList(false, null);
    case "admin_attempts": return renderResultsList(true, state.viewUserId);
    case "result_detail": return renderResultDetail();
    case "admin_users": return renderAdminUsers();
    case "stats": return renderStats();
    case "leaderboard": return renderLeaderboard();
    default: return renderMain();
  }
}

function header(title, subtitle, showBack) {
  return `
    <div class="header">
      ${showBack ? `<button class="back-btn" id="btn-back">←</button>` : ""}
      <div style="flex:1;min-width:0;">
        <h1>${title}</h1>
        ${subtitle ? `<p class="subtitle">${subtitle}</p>` : ""}
      </div>
      <button class="lang-btn" id="btn-lang">${LANG_META[LANG].flag}</button>
    </div>`;
}

function bindHeaderControls() {
  const back = document.getElementById("btn-back");
  if (back) back.onclick = goBack;
  const langBtn = document.getElementById("btn-lang");
  if (langBtn) langBtn.onclick = showLanguageModal;
}

// ---------- Tilni tanlash (birinchi kirishda) ----------
function renderLanguageSelect() {
  appEl.innerHTML = `
    <div class="header" style="padding-top:24px;">
      <div>
        <h1>Tilni tanlang / Выберите язык / Choose language</h1>
      </div>
    </div>
    <div class="lang-select-grid">
      ${LANGS.map((code) => `
        <div class="lang-select-card" data-lang="${code}">
          <div class="flag-big">${LANG_META[code].flag}</div>
          <div class="lang-name">${LANG_META[code].name}</div>
          <div class="chevron">›</div>
        </div>
      `).join("")}
    </div>
  `;
  document.querySelectorAll(".lang-select-card").forEach((el) => {
    el.onclick = () => {
      LANG = el.dataset.lang;
      storeLanguage(LANG);
      document.documentElement.lang = LANG;
      state.screen = ME.registered ? "main" : "register";
      render();
    };
  });
}

// ---------- Ro'yxatdan o'tish ----------
function renderRegister() {
  appEl.innerHTML = `
    ${header(t("registerTitle"), t("registerSubtitle"))}
    <div class="form-group">
      <label>${t("firstNameLabel")}</label>
      <input id="f_first" type="text" placeholder="${t("firstNamePlaceholder")}" />
    </div>
    <div class="form-group">
      <label>${t("lastNameLabel")}</label>
      <input id="f_last" type="text" placeholder="${t("lastNamePlaceholder")}" />
    </div>
    <div class="form-group">
      <label>${t("fatherNameLabel")}</label>
      <input id="f_father" type="text" placeholder="${t("fatherNamePlaceholder")}" />
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>${t("dayLabel")}</label>
        <select id="f_day">${optionsRange(1, 31)}</select>
      </div>
      <div class="form-group">
        <label>${t("monthLabel")}</label>
        <select id="f_month">${optionsRange(1, 12)}</select>
      </div>
      <div class="form-group">
        <label>${t("yearLabel")}</label>
        <select id="f_year">${optionsRange(2025, 1950, true)}</select>
      </div>
    </div>
    <div id="reg-error" style="color:var(--red);font-size:13px;margin-bottom:10px;"></div>
    <button class="btn btn-primary" id="btn-register">${t("continueBtn")}</button>
  `;
  bindHeaderControls();
  document.getElementById("btn-register").onclick = onRegisterSubmit;
}

function optionsRange(start, end, desc) {
  const arr = [];
  if (desc) {
    for (let i = start; i >= end; i--) arr.push(i);
  } else {
    for (let i = start; i <= end; i++) arr.push(i);
  }
  return arr.map((v) => `<option value="${v}">${v}</option>`).join("");
}

async function onRegisterSubmit() {
  const first_name = document.getElementById("f_first").value.trim();
  const last_name = document.getElementById("f_last").value.trim();
  const father_name = document.getElementById("f_father").value.trim();
  const birth_day = parseInt(document.getElementById("f_day").value, 10);
  const birth_month = parseInt(document.getElementById("f_month").value, 10);
  const birth_year = parseInt(document.getElementById("f_year").value, 10);
  const errEl = document.getElementById("reg-error");

  if (!first_name || !last_name || !father_name) {
    errEl.textContent = t("fillAllFields");
    return;
  }
  try {
    const res = await api("/api/register", {
      method: "POST",
      body: { first_name, last_name, father_name, birth_day, birth_month, birth_year, language: LANG },
    });
    ME = { ...ME, registered: true, profile: res.profile };
    state.navStack = [];
    state.screen = "main";
    render();
  } catch (e) {
    errEl.textContent = e.message;
  }
}

// ---------- Asosiy menyu ----------
function renderMain() {
  const name = ME.profile ? `${ME.profile.first_name}` : "";
  let rows = CONFIG.sections.map((s) => `
    <div class="menu-row" data-section="${s.key}">
      <div class="icon-badge" style="background:${s.color}">${s.icon}</div>
      <div>
        <div class="title">${sectionLabel(s.key)}</div>
        <div class="desc">${sectionDescText(s.key)}</div>
      </div>
      <div class="chevron">›</div>
    </div>
  `).join("");
  rows += `
    <div class="menu-row" id="row-results">
      <div class="icon-badge" style="background:#14b8a6">📊</div>
      <div>
        <div class="title">${t("myResultsTitle")}</div>
        <div class="desc">${t("myResultsDesc")}</div>
      </div>
      <div class="chevron">›</div>
    </div>
    <div class="menu-row" id="row-stats">
      <div class="icon-badge" style="background:#7c3aed">🔥</div>
      <div>
        <div class="title">${t("statsTitle")}</div>
        <div class="desc">${t("statsDesc")}</div>
      </div>
      <div class="chevron">›</div>
    </div>
  `;
  if (ME.is_admin) {
    rows += `
      <div class="menu-row" id="row-admin">
        <div class="icon-badge" style="background:#0f172a">🛡</div>
        <div>
          <div class="title">${t("adminPanelTitle")}</div>
          <div class="desc">${t("adminPanelDesc")}</div>
        </div>
        <div class="chevron">›</div>
      </div>
    `;
  }
  appEl.innerHTML = `
    ${header(t("mainGreeting")(escapeHtml(name)), t("mainSubtitle"), false)}
    ${rows}
  `;
  bindHeaderControls();
  document.querySelectorAll(".menu-row[data-section]").forEach((el) => {
    el.onclick = () => {
      state.selection = { section: el.dataset.section, operation: null, digits: null, timePerQuestion: null };
      pushScreen("section");
    };
  });
  document.getElementById("row-results").onclick = () => pushScreen("my_results");
  document.getElementById("row-stats").onclick = () => pushScreen("stats");
  const adminRow = document.getElementById("row-admin");
  if (adminRow) adminRow.onclick = () => pushScreen("admin_users");
}

// ---------- Bo'lim ichidagi amallar (Arifmetika / Kasrlar / ...) ----------
function renderSection() {
  const sectionKey = state.selection.section;
  const opKeys = Object.keys(CONFIG.operations).filter((k) => CONFIG.operations[k].section === sectionKey);
  const cards = opKeys.map((key) => {
    const op = CONFIG.operations[key];
    return `
      <div class="section-card" data-op="${key}" style="border-color:${op.color}22">
        <div class="icon-badge" style="background:${op.color}">${OP_EMOJI[key] || op.symbol}</div>
        <div class="title">${opLabel(key)}</div>
        <div class="desc">${sectionCardDesc(sectionKey)}</div>
      </div>`;
  }).join("");

  appEl.innerHTML = `
    ${header(sectionLabel(sectionKey), t("chooseOperationSubtitle"), true)}
    <div class="card-grid">${cards}</div>
  `;
  bindHeaderControls();
  document.querySelectorAll(".section-card").forEach((el) => {
    el.onclick = () => {
      state.selection.operation = el.dataset.op;
      pushScreen("digits");
    };
  });
}

// ---------- Xona / daraja tanlash ----------
async function renderDigits() {
  const op = CONFIG.operations[state.selection.operation];
  const useLevelWording = op.section !== "arithmetic";

  const renderButtons = (recommended) => {
    const buttons = [];
    for (let d = CONFIG.min_digits; d <= CONFIG.max_digits; d++) {
      const label = useLevelWording ? t("levelLabel")(d) : t("digitLabel")(d);
      const badge = d === recommended ? `<div class="recommend-badge">${t("recommendedBadge")}</div>` : "";
      buttons.push(`<button class="choice-btn${d === recommended ? " recommended" : ""}" data-d="${d}">${badge}${label}</button>`);
    }
    appEl.innerHTML = `
      ${header(opLabel(state.selection.operation), useLevelWording ? t("chooseLevelSubtitle") : t("chooseDigitsSubtitle"), true)}
      <div class="choice-grid">${buttons.join("")}</div>
    `;
    bindHeaderControls();
    document.querySelectorAll(".choice-btn").forEach((el) => {
      el.onclick = () => {
        state.selection.digits = parseInt(el.dataset.d, 10);
        pushScreen("time");
      };
    });
  };

  renderButtons(null);
  try {
    const rec = await api(`/api/recommend?operation=${encodeURIComponent(state.selection.operation)}`);
    if (rec.suggested_level && state.screen === "digits") {
      renderButtons(rec.suggested_level);
    }
  } catch (e) {
    // tavsiya ixtiyoriy — xato bo'lsa jim o'tkazib yuboriladi
  }
}

// ---------- Vaqt tanlash ----------
function renderTime() {
  const op = CONFIG.operations[state.selection.operation];
  const useLevelWording = op.section !== "arithmetic";
  const levelText = useLevelWording ? t("levelLabel")(state.selection.digits) : t("digitLabel")(state.selection.digits);
  const buttons = CONFIG.time_options
    .map((tOpt) => `<button class="choice-btn" data-s="${tOpt.seconds}">${timeLabel(tOpt.seconds)}</button>`)
    .join("");
  appEl.innerHTML = `
    ${header(opLabel(state.selection.operation), t("chooseTimeSubtitle")(levelText), true)}
    <div class="choice-grid">${buttons}</div>
  `;
  bindHeaderControls();
  document.querySelectorAll(".choice-btn").forEach((el) => {
    el.onclick = async () => {
      state.selection.timePerQuestion = parseInt(el.dataset.s, 10);
      await startTest();
    };
  });
}

// ---------- Test boshlash ----------
async function startTest() {
  try {
    const res = await api("/api/tests/start", {
      method: "POST",
      body: {
        operation: state.selection.operation,
        digits: state.selection.digits,
        time_per_question: state.selection.timePerQuestion,
      },
    });
    state.test = res;
    state.pendingChoice = null;
    state.lastFeedback = null;
    state.navStack = [];
    state.screen = "test";
    render();
    startTimer();
  } catch (e) {
    alert(e.message);
  }
}

// ---------- Test ekrani ----------
function renderTest() {
  const t_ = state.test;
  const q = t_.question;
  const correctPct = t_.total_questions ? (t_.progress.correct / t_.total_questions) * 100 : 0;
  const wrongPct = t_.total_questions ? (t_.progress.wrong / t_.total_questions) * 100 : 0;
  const instruction = instructionFor(q.operation);
  const bigChoices = BIG_CHOICE_OPS.has(q.operation);
  const wordProblem = WORD_PROBLEM_OPS.has(q.operation) || !!q.display_text;

  appEl.innerHTML = `
    <div class="test-topbar">
      <div class="progress-line">
        <span>${t("progressLine")(t_.progress.answered, t_.total_questions)}</span>
        <span><span class="stat-correct">✔ ${t_.progress.correct}</span> &nbsp; <span class="stat-wrong">✘ ${t_.progress.wrong}</span></span>
      </div>
      <div class="progress-bar-track">
        <div class="progress-bar-fill-correct" style="width:${correctPct}%"></div>
        <div class="progress-bar-fill-wrong" style="width:${wrongPct}%"></div>
      </div>
      <div class="timer-wrap">
        <div class="timer-bar-track"><div class="timer-bar-fill" id="timer-fill"></div></div>
        <div class="timer-label" id="timer-label">--</div>
      </div>
    </div>
    ${state.lastFeedback ? renderFeedbackBanner() : ""}
    <div class="question-card${wordProblem ? " word-problem" : ""}">
      ${instruction ? `<div class="question-instruction">${instruction}</div>` : ""}
      <div>${questionExprHtml(q)}${questionSuffix(q)}</div>
    </div>
    <div class="answer-grid" id="answer-grid">
      ${q.choices.map((c, i) => `<button class="answer-btn${bigChoices ? " compare-btn" : ""}" data-c="${escapeHtml(c)}" data-i="${i}">${escapeHtml(translateChoiceLabel(q.operation, c))}</button>`).join("")}
    </div>
    <button class="btn btn-danger-outline" id="btn-finish-test" style="margin-top:18px;">${t("finishTestBtn")}</button>
  `;

  document.querySelectorAll(".answer-btn").forEach((el) => {
    el.onclick = () => onChooseAnswer(el.dataset.c);
  });
  document.getElementById("btn-finish-test").onclick = showFinishConfirmModal;
}

function showFinishConfirmModal() {
  const t_ = state.test;
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "finish-modal";
  modal.innerHTML = `
    <div class="modal-sheet">
      <h3>${t("finishModalTitle")}</h3>
      <p>${t("finishModalBody")(t_.progress.answered, t_.total_questions)}</p>
      <div class="btn-row">
        <button class="btn btn-outline" id="btn-finish-cancel">${t("finishModalCancel")}</button>
        <button class="btn btn-danger-outline" id="btn-finish-confirm">${t("finishModalConfirm")}</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  document.getElementById("btn-finish-cancel").onclick = () => modal.remove();
  document.getElementById("btn-finish-confirm").onclick = async () => {
    modal.remove();
    await finishTestEarly();
  };
}

async function finishTestEarly() {
  stopTimer();
  try {
    const res = await api(`/api/tests/${state.test.attempt_id}/finish`, { method: "POST" });
    state.test.progress = res.progress;
    state.test.finished = true;
    state.test.streak = res.streak;
    state.test.newAchievements = res.new_achievements || [];
    state.lastFeedback = null;
    state.screen = "test_result";
    render();
  } catch (e) {
    alert(e.message);
  }
}

function explanationHtml(fb) {
  const fn = EXPLANATIONS[fb.operation];
  if (!fn || !fb.question) return "";
  try {
    const text = fn(fb.question, fb.correctAnswer);
    if (!text) return "";
    return `<div class="explanation-box"><b>${t("explanationLabel")}</b> ${text}</div>`;
  } catch (e) {
    return "";
  }
}

function renderFeedbackBanner() {
  const fb = state.lastFeedback;
  const correctDisplay = dash(translateChoiceLabel(fb.operation, fb.correctAnswer));
  const chosenDisplay = dash(translateChoiceLabel(fb.operation, fb.chosen));
  if (fb.timedOut) {
    return `<div class="feedback-banner wrong">${t("timedOutFeedback")(correctDisplay)}</div>${explanationHtml(fb)}`;
  }
  if (fb.isCorrect) {
    return `<div class="feedback-banner correct">${t("correctFeedback")}</div>`;
  }
  return `<div class="feedback-banner wrong">${t("wrongFeedback")(chosenDisplay, correctDisplay)}</div>${explanationHtml(fb)}`;
}

function onChooseAnswer(value) {
  state.pendingChoice = value;
  showConfirmModal();
}

function showConfirmModal() {
  const op = state.test.question.operation;
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "confirm-modal";
  modal.innerHTML = `
    <div class="modal-sheet">
      <h3>${t("confirmModalTitle")(dash(translateChoiceLabel(op, state.pendingChoice)))}</h3>
      <p>${t("confirmModalBody")}</p>
      <div class="btn-row">
        <button class="btn btn-outline" id="btn-rethink">${t("rethinkBtn")}</button>
        <button class="btn btn-success" id="btn-confirm">${t("confirmBtn")}</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  document.getElementById("btn-rethink").onclick = () => {
    state.pendingChoice = null;
    modal.remove();
  };
  document.getElementById("btn-confirm").onclick = () => {
    modal.remove();
    confirmAnswer(false);
  };
}

let answerLocked = false;

async function confirmAnswer(timedOut) {
  if (answerLocked) return;
  answerLocked = true;
  stopTimer();

  const t_ = state.test;
  const q = t_.question;
  const chosen = timedOut ? null : state.pendingChoice;
  const timeTaken = t_.time_per_question * 1000 - Math.max(0, state.timer.deadline - Date.now());

  // javob tugmalarini vizual belgilash
  document.querySelectorAll(".answer-btn").forEach((el) => {
    el.disabled = true;
    if (el.dataset.c === chosen) el.classList.add("selected");
  });

  try {
    const res = await api("/api/tests/answer", {
      method: "POST",
      body: {
        question_id: q.id,
        selected_answer: chosen,
        time_taken_ms: Math.max(0, Math.round(timeTaken)),
        timed_out: timedOut,
      },
    });

    // to'g'ri/xato ranglarni ko'rsatish
    document.querySelectorAll(".answer-btn").forEach((el) => {
      if (el.dataset.c === String(res.correct_answer)) el.classList.add("correct");
      else if (el.dataset.c === chosen) el.classList.add("wrong");
    });

    state.lastFeedback = {
      isCorrect: res.is_correct,
      correctAnswer: res.correct_answer,
      chosen,
      timedOut,
      operation: q.operation,
      question: q,
    };

    t_.progress = res.progress;
    if (res.finished) {
      state.test.streak = res.streak;
      state.test.newAchievements = res.new_achievements || [];
    }

    setTimeout(() => {
      answerLocked = false;
      state.pendingChoice = null;
      if (res.finished) {
        state.test.finished = true;
        state.screen = "test_result";
        render();
      } else {
        state.test.question = res.next_question;
        state.lastFeedback = null;
        render();
        startTimer();
      }
    }, 1400);
  } catch (e) {
    answerLocked = false;
    alert(e.message);
  }
}

// ---------- Timer ----------
function startTimer() {
  stopTimer();
  const seconds = state.test.time_per_question;
  state.timer.total = seconds * 1000;
  state.timer.deadline = Date.now() + seconds * 1000;
  tick();
}

function stopTimer() {
  if (state.timer.raf) {
    cancelAnimationFrame(state.timer.raf);
    state.timer.raf = null;
  }
}

function tick() {
  const fillEl = document.getElementById("timer-fill");
  const labelEl = document.getElementById("timer-label");
  if (!fillEl || !labelEl) return;

  const remainingMs = Math.max(0, state.timer.deadline - Date.now());
  const pct = (remainingMs / state.timer.total) * 100;
  const remainingSec = Math.ceil(remainingMs / 1000);

  fillEl.style.width = pct + "%";
  labelEl.textContent = formatSeconds(remainingSec);

  labelEl.classList.remove("warn", "danger");
  fillEl.style.background = "var(--green)";
  if (pct <= 50 && pct > 20) {
    fillEl.style.background = "var(--yellow)";
    labelEl.classList.add("warn");
  } else if (pct <= 20) {
    fillEl.style.background = "var(--red)";
    labelEl.classList.add("danger");
  }

  if (remainingMs <= 0) {
    confirmAnswer(true);
    return;
  }
  state.timer.raf = requestAnimationFrame(tick);
}

function formatSeconds(total) {
  const m = Math.floor(total / 60);
  const s = total % 60;
  if (m > 0) return `${m}:${String(s).padStart(2, "0")}`;
  return `${s}s`;
}

// ---------- Test yakuni ----------
function renderTestResult() {
  const t_ = state.test;
  const total = t_.total_questions;
  const answered = t_.progress.answered;
  const correct = t_.progress.correct;
  const wrong = t_.progress.wrong;
  const early = answered < total;
  const good = answered > 0 && correct / answered >= 0.7;
  const summaryLine = early
    ? t("summaryEarly")(total, answered, correct, wrong)
    : t("summaryFull")(total, correct, wrong);

  let toasts = "";
  if (t_.streak && t_.streak.current > 1) {
    toasts += `<div class="toast-banner streak">${t("streakToast")(t_.streak.current)}</div>`;
  }
  const dict = I18N[LANG] || I18N.uz;
  (t_.newAchievements || []).forEach((key) => {
    const meta = dict.achievements[key];
    if (meta) toasts += `<div class="toast-banner achievement">${t("newAchievementToast")(`${meta.icon} ${meta.label}`)}</div>`;
  });

  appEl.innerHTML = `
    ${header(t("testFinishedTitle"))}
    <div class="feedback-banner ${good ? "correct" : "wrong"}" style="font-size:18px;padding:22px;">
      ${summaryLine}
    </div>
    ${toasts}
    <button class="btn btn-primary" id="btn-detail">${t("detailBtn")}</button>
    <div style="height:10px"></div>
    <button class="btn btn-outline" id="btn-home">${t("homeBtn")}</button>
  `;
  bindHeaderControls();
  document.getElementById("btn-detail").onclick = () => {
    state.viewAttemptId = t_.attempt_id;
    state.navStack = [];
    pushScreen("result_detail");
  };
  document.getElementById("btn-home").onclick = () => {
    state.navStack = [];
    state.screen = "main";
    render();
  };
}

// ---------- Natijalar ro'yxati (o'zim / admin) ----------
async function renderResultsList(isAdminView, userId) {
  appEl.innerHTML = `${header(isAdminView ? t("adminPanelTitle") : t("myResultsTitle"), null, true)}<div class="empty-state">${t("loading")}</div>`;
  bindHeaderControls();
  try {
    const res = isAdminView
      ? await api(`/api/admin/users/${userId}/attempts`)
      : await api("/api/results");
    const attempts = res.attempts;
    const title = isAdminView
      ? t("userTestsTitle")(`${res.user.last_name} ${res.user.first_name}`)
      : t("myResultsTitle");

    if (!attempts.length) {
      appEl.innerHTML = `${header(title, null, true)}<div class="empty-state">${t("noTestsYet")}</div>`;
      bindHeaderControls();
      return;
    }

    const rows = attempts.map((a) => {
      const ratio = a.total_questions ? a.correct_count / a.total_questions : 0;
      const scoreClass = ratio >= 0.7 ? "good" : ratio >= 0.4 ? "mid" : "bad";
      const op = CONFIG.operations[a.operation] || {};
      const date = (a.finished_at || a.started_at || "").replace("T", " ").slice(0, 16);
      return `
        <div class="result-row" data-id="${a.id}">
          <div class="icon-badge" style="background:${op.color || "#6366f1"};width:40px;height:40px;font-size:18px;">${OP_EMOJI[a.operation] || "❓"}</div>
          <div class="meta">
            <div class="title">${opLabel(a.operation)}</div>
            <div class="date">${date}</div>
          </div>
          <div class="score ${scoreClass}">${a.correct_count}/${a.total_questions}</div>
        </div>`;
    }).join("");

    appEl.innerHTML = `${header(title, null, true)}<div>${rows}</div>`;
    bindHeaderControls();
    document.querySelectorAll(".result-row").forEach((el) => {
      el.onclick = () => {
        state.viewAttemptId = parseInt(el.dataset.id, 10);
        pushScreen("result_detail");
      };
    });
  } catch (e) {
    appEl.innerHTML = `${header(t("errorTitle"), null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindHeaderControls();
  }
}

// ---------- Natija tafsiloti ----------
async function renderResultDetail() {
  appEl.innerHTML = `${header(t("detailBtn"), null, true)}<div class="empty-state">${t("loading")}</div>`;
  bindHeaderControls();
  try {
    const res = await api(`/api/results/${state.viewAttemptId}`);
    const a = res.attempt;
    const ownerLine = ME.is_admin && res.owner
      ? `<p class="subtitle">${res.owner.last_name} ${res.owner.first_name} ${res.owner.father_name}</p>`
      : "";

    const rows = res.questions.map((q) => {
      let statusClass = "wrong";
      let line;
      const correctDisplay = dash(translateChoiceLabel(q.operation, q.correct_answer));
      const selectedDisplay = dash(translateChoiceLabel(q.operation, q.selected_answer));
      if (q.status === "pending") {
        statusClass = "";
        line = `<span class="ans-line">${t("noAnswer")}</span>`;
      } else if (q.status === "timeout") {
        line = `<span class="ans-line">${t("timeoutLine")(`<span class="correct-val">${correctDisplay}</span>`)}</span>`;
      } else if (q.is_correct) {
        statusClass = "correct";
        line = `<span class="ans-line">${t("yourAnswerCorrect")(`<span class="chosen-correct">${selectedDisplay}</span>`)}</span>`;
      } else {
        statusClass = "wrong";
        line = `<span class="ans-line">${t("yourAnswerWrong")(`<span class="chosen-wrong">${selectedDisplay}</span>`, `<span class="correct-val">${correctDisplay}</span>`)}</span>`;
      }
      return `
        <div class="detail-q-row ${statusClass}">
          <div class="expr">${q.order_index + 1}) ${questionExprHtml(q)}${questionSuffix(q)}</div>
          ${line}
        </div>`;
    }).join("");

    appEl.innerHTML = `
      ${header(opLabel(a.operation), null, true)}
      ${ownerLine}
      <div class="feedback-banner correct" style="margin-bottom:16px;">
        ${t("resultSummary")(a.total_questions, a.correct_count, a.wrong_count)}
      </div>
      ${rows}
    `;
    bindHeaderControls();
  } catch (e) {
    appEl.innerHTML = `${header(t("errorTitle"), null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindHeaderControls();
  }
}

// ---------- Admin: foydalanuvchilar ----------
async function renderAdminUsers() {
  appEl.innerHTML = `${header(t("adminPanelTitle"), t("adminPanelDesc"), true)}<div class="empty-state">${t("loading")}</div>`;
  bindHeaderControls();
  try {
    const res = await api("/api/admin/users");
    const exportBtn = `<button class="btn btn-outline" id="btn-admin-export" style="margin-bottom:14px;">${t("adminExportBtn")}</button>`;
    if (!res.users.length) {
      appEl.innerHTML = `${header(t("adminPanelTitle"), t("adminPanelDesc"), true)}${exportBtn}<div class="empty-state">${t("noUsersYet")}</div>`;
      bindHeaderControls();
      bindAdminExportBtn();
      return;
    }
    const rows = res.users.map((u) => `
      <div class="admin-user-row" data-id="${u.telegram_id}">
        <div class="name">${u.last_name} ${u.first_name} ${u.father_name}${u.is_admin ? " 🛡" : ""}</div>
        <div class="sub">${u.username ? "@" + u.username : t("noUsername")} · ${t("testsCountSuffix")(u.attempts_count)}</div>
        <div class="stats"><span class="c">✔ ${u.total_correct}</span><span class="w">✘ ${u.total_wrong}</span></div>
      </div>`).join("");
    appEl.innerHTML = `${header(t("adminPanelTitle"), t("adminPanelDesc"), true)}${exportBtn}<div>${rows}</div>`;
    bindHeaderControls();
    bindAdminExportBtn();
    document.querySelectorAll(".admin-user-row").forEach((el) => {
      el.onclick = () => {
        state.viewUserId = parseInt(el.dataset.id, 10);
        pushScreen("admin_attempts");
      };
    });
  } catch (e) {
    appEl.innerHTML = `${header(t("errorTitle"), null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindHeaderControls();
  }
}

function bindAdminExportBtn() {
  const btn = document.getElementById("btn-admin-export");
  if (!btn) return;
  btn.onclick = async () => {
    btn.disabled = true;
    try {
      const res = await fetch("/api/admin/export", {
        headers: { "X-Telegram-Init-Data": INIT_DATA },
      });
      if (!res.ok) throw new Error(t("genericError"));
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "mathbot_foydalanuvchilar.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (e) {
      alert(e.message);
    } finally {
      btn.disabled = false;
    }
  };
}

// ---------- Statistikam: seriya, yutuqlar, mavzular, referral ----------
async function renderStats() {
  appEl.innerHTML = `${header(t("statsTitle"), t("statsDesc"), true)}<div class="empty-state">${t("loading")}</div>`;
  bindHeaderControls();
  try {
    const res = await api("/api/stats");
    const dict = I18N[LANG] || I18N.uz;

    const rankHtml = res.rank
      ? `${t("rankLine")(res.rank.rank, res.rank.points)}<button class="btn btn-outline" id="btn-view-leaderboard" style="margin-top:10px;">${t("viewLeaderboardBtn")}</button>`
      : `${t("noRankYet")}`;

    const topicRows = res.topic_stats.length
      ? res.topic_stats.map((ts) => `
          <div class="topic-stat-row">
            <div class="topic-stat-label">${sectionLabel(ts.section)}</div>
            <div class="topic-stat-bar-track"><div class="topic-stat-bar-fill" style="width:${ts.accuracy}%"></div></div>
            <div class="topic-stat-pct">${ts.accuracy}%</div>
          </div>`).join("")
      : `<div class="empty-state">${t("noTopicStatsYet")}</div>`;

    const achievementCards = res.achievements.map((a) => {
      const meta = dict.achievements[a.key] || { icon: "🏅", label: a.key };
      return `<div class="achievement-card${a.earned ? " earned" : ""}">
        <div class="ach-icon">${meta.icon}</div>
        <div class="ach-label">${meta.label}</div>
      </div>`;
    }).join("");

    const referralLinkHtml = res.referral.link
      ? `<div class="referral-code" id="referral-copy-target">${escapeHtml(res.referral.link)}</div>`
      : `<div class="referral-code" id="referral-copy-target">${escapeHtml(res.referral.code)}</div><div style="font-size:12px;color:var(--hint);margin-top:6px;">${t("referralNoLink")}</div>`;

    appEl.innerHTML = `
      ${header(t("statsTitle"), t("statsDesc"), true)}
      <div class="stat-card">
        <div class="stat-card-title">${t("streakCardTitle")}</div>
        <div>${t("streakCurrent")(res.streak.current)}</div>
        <div style="margin-top:4px;">${t("streakLongest")(res.streak.longest)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-title">${t("rankCardTitle")}</div>
        <div>${rankHtml}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-title">${t("topicStatsTitle")}</div>
        ${topicRows}
      </div>
      <div class="stat-card">
        <div class="stat-card-title">${t("achievementsTitle")}</div>
        <div class="achievement-grid">${achievementCards}</div>
      </div>
      <div class="stat-card">
        <div class="stat-card-title">${t("referralCardTitle")}</div>
        <div style="font-size:13px;color:var(--hint);margin-bottom:8px;">${t("referralDesc")}</div>
        <div style="margin-bottom:8px;">${t("referralCount")(res.referral.count)}</div>
        <div style="font-size:12px;color:var(--hint);margin-bottom:4px;">${t("referralCodeLabel")}</div>
        ${referralLinkHtml}
        <button class="btn btn-outline" id="btn-copy-referral" style="margin-top:10px;">${t("copyBtn")}</button>
      </div>
    `;
    bindHeaderControls();
    const lbBtn = document.getElementById("btn-view-leaderboard");
    if (lbBtn) lbBtn.onclick = () => pushScreen("leaderboard");
    const copyBtn = document.getElementById("btn-copy-referral");
    if (copyBtn) {
      copyBtn.onclick = async () => {
        const text = document.getElementById("referral-copy-target").textContent;
        try {
          await navigator.clipboard.writeText(text);
          copyBtn.textContent = t("copiedMsg");
          setTimeout(() => { copyBtn.textContent = t("copyBtn"); }, 1500);
        } catch (e) {
          alert(text);
        }
      };
    }
  } catch (e) {
    appEl.innerHTML = `${header(t("errorTitle"), null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindHeaderControls();
  }
}

// ---------- Reyting (leaderboard) ----------
async function renderLeaderboard() {
  appEl.innerHTML = `${header(t("leaderboardTitle"), t("leaderboardDesc"), true)}<div class="empty-state">${t("loading")}</div>`;
  bindHeaderControls();
  try {
    const res = await api("/api/leaderboard");
    if (!res.top.length) {
      appEl.innerHTML = `${header(t("leaderboardTitle"), t("leaderboardDesc"), true)}<div class="empty-state">${t("noLeaderboardYet")}</div>`;
      bindHeaderControls();
      return;
    }
    const medals = ["🥇", "🥈", "🥉"];
    const rows = res.top.map((r, i) => `
      <div class="leaderboard-row">
        <div class="lb-rank">${medals[i] || (i + 1)}</div>
        <div class="lb-name">${escapeHtml(r.first_name)} ${escapeHtml(r.last_name)}</div>
        <div class="lb-points">${t("pointsSuffix")(r.points)}</div>
      </div>`).join("");
    const myRankLine = res.my_rank
      ? `<div class="stat-card">${t("rankLine")(res.my_rank.rank, res.my_rank.points)}</div>`
      : "";
    appEl.innerHTML = `${header(t("leaderboardTitle"), t("leaderboardDesc"), true)}${myRankLine}<div>${rows}</div>`;
    bindHeaderControls();
  } catch (e) {
    appEl.innerHTML = `${header(t("errorTitle"), null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindHeaderControls();
  }
}

init();
