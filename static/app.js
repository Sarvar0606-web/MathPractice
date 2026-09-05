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
};

// Bu amallarning javob variantlari bitta belgi/qisqa satr (masalan "<", ">", "=")
// bo'lgani uchun javob tugmalarida kattaroq shrift ishlatiladi.
const BIG_CHOICE_OPS = new Set(["compare", "frac_compare"]);

// Bular to'liq gap (masala) shaklida so'raladi — matn kichikroq va chapga
// tekislangan holda ko'rsatiladi.
const WORD_PROBLEM_OPS = new Set([
  "percent_of", "percent_find_whole", "percent_increase",
  "percent_discount", "percent_profit_loss", "percent_successive",
]);

// "= ?" qo'shilmaydigan amallar (natija emas, aylantirish/qisqartirish so'raladi,
// javob solishtirish belgisi bo'ladi, yoki savol allaqachon "?" bilan tugaydi)
const NO_SUFFIX_OPS = new Set([
  "compare", "frac_compare", "frac_simplify", "frac_mixed", "frac_decimal",
  ...WORD_PROBLEM_OPS,
]);

const QUESTION_INSTRUCTIONS = {
  frac_simplify: "Kasrni qisqartiring:",
  frac_mixed: "Aralash songa aylantiring:",
  frac_decimal: "O'nli kasrga aylantiring:",
};

let CONFIG = null;
let ME = null; // {telegram_id, registered, profile, is_admin}

const state = {
  screen: "loading",
  selection: { section: null, operation: null, digits: null, timePerQuestion: null },
  test: null, // {attempt_id, total_questions, time_per_question, question, progress}
  timer: { deadline: 0, raf: null, total: 0 },
  pendingChoice: null, // tanlangan-lekin-hali-tasdiqlanmagan javob
  lastFeedback: null, // {isCorrect, correctAnswer, chosen, timedOut}
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
    let msg = "Xatolik yuz berdi";
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
    if (!ME.registered) {
      state.screen = "register";
    } else {
      state.screen = "main";
    }
  } catch (e) {
    appEl.innerHTML = `<div class="empty-state">Xatolik: ${escapeHtml(e.message)}<br/>Iltimos, botni Telegram ichida oching.</div>`;
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
  switch (q.operation) {
    case "add": case "sub": case "mul": case "div": {
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
    case "percent_of":
      return `${q.a} ning <b>${q.b}%</b> i nechiga teng?`;
    case "percent_find_whole":
      return `Biror sonning <b>${q.b}%</b> i ${q.a} ga teng. O'sha son nechiga teng?`;
    case "percent_increase":
      return `${q.a} so'm bo'lgan narx <b>${q.b}%</b> ga oshdi. Yangi narx nechiga teng?`;
    case "percent_discount":
      return `${q.a} so'm bo'lgan mahsulotga <b>${q.b}%</b> chegirma qilindi. Chegirmadagi narx nechiga teng?`;
    case "percent_profit_loss":
      return `Tannarxi ${q.a} so'm bo'lgan mahsulot ${q.b} so'mga sotildi. Foyda yoki zarar necha foiz bo'ldi?`;
    case "percent_successive": {
      const dir1 = q.b >= 0 ? "oshdi" : "kamaydi";
      const dir2 = q.c >= 0 ? "oshdi" : "kamaydi";
      return `${q.a} dastlab <b>${Math.abs(q.b)}%</b> ga ${dir1}, keyin <b>${Math.abs(q.c)}%</b> ga ${dir2}. Oxirgi qiymat nechiga teng?`;
    }
    default:
      return `${q.a} ? ${q.b}`;
  }
}

function questionSuffix(q) {
  return NO_SUFFIX_OPS.has(q.operation) ? "" : " = ?";
}

// ---------- Render dispatch ----------
function render() {
  switch (state.screen) {
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
    default: return renderMain();
  }
}

function header(title, subtitle, showBack) {
  return `
    <div class="header">
      ${showBack ? `<button class="back-btn" id="btn-back">←</button>` : ""}
      <div>
        <h1>${title}</h1>
        ${subtitle ? `<p class="subtitle">${subtitle}</p>` : ""}
      </div>
    </div>`;
}

function bindBack() {
  const btn = document.getElementById("btn-back");
  if (btn) btn.onclick = goBack;
}

// ---------- Ro'yxatdan o'tish ----------
function renderRegister() {
  appEl.innerHTML = `
    ${header("Ro'yxatdan o'tish", "Testlarni boshlashdan oldin ma'lumotlaringizni kiriting")}
    <div class="form-group">
      <label>Ism</label>
      <input id="f_first" type="text" placeholder="Ismingiz" />
    </div>
    <div class="form-group">
      <label>Familiya</label>
      <input id="f_last" type="text" placeholder="Familiyangiz" />
    </div>
    <div class="form-group">
      <label>Otasining ismi (Sharif)</label>
      <input id="f_father" type="text" placeholder="Otangizning ismi" />
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Kun</label>
        <select id="f_day">${optionsRange(1, 31)}</select>
      </div>
      <div class="form-group">
        <label>Oy</label>
        <select id="f_month">${optionsRange(1, 12)}</select>
      </div>
      <div class="form-group">
        <label>Yil</label>
        <select id="f_year">${optionsRange(2025, 1950, true)}</select>
      </div>
    </div>
    <div id="reg-error" style="color:var(--red);font-size:13px;margin-bottom:10px;"></div>
    <button class="btn btn-primary" id="btn-register">Davom etish</button>
  `;
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
    errEl.textContent = "Iltimos, barcha maydonlarni to'ldiring.";
    return;
  }
  try {
    const res = await api("/api/register", {
      method: "POST",
      body: { first_name, last_name, father_name, birth_day, birth_month, birth_year },
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
        <div class="title">${s.label}</div>
        <div class="desc">${s.desc}</div>
      </div>
      <div class="chevron">›</div>
    </div>
  `).join("");
  rows += `
    <div class="menu-row" id="row-results">
      <div class="icon-badge" style="background:#14b8a6">📊</div>
      <div>
        <div class="title">Natijalarim</div>
        <div class="desc">Yechilgan testlar tarixi</div>
      </div>
      <div class="chevron">›</div>
    </div>
  `;
  if (ME.is_admin) {
    rows += `
      <div class="menu-row" id="row-admin">
        <div class="icon-badge" style="background:#0f172a">🛡</div>
        <div>
          <div class="title">Admin panel</div>
          <div class="desc">Barcha foydalanuvchilar natijalari</div>
        </div>
        <div class="chevron">›</div>
      </div>
    `;
  }
  appEl.innerHTML = `
    ${header(`Salom, ${escapeHtml(name)} 👋`, "Nima bilan shug'ullanamiz?", false)}
    ${rows}
  `;
  document.querySelectorAll(".menu-row[data-section]").forEach((el) => {
    el.onclick = () => {
      state.selection = { section: el.dataset.section, operation: null, digits: null, timePerQuestion: null };
      pushScreen("section");
    };
  });
  document.getElementById("row-results").onclick = () => pushScreen("my_results");
  const adminRow = document.getElementById("row-admin");
  if (adminRow) adminRow.onclick = () => pushScreen("admin_users");
}

// ---------- Bo'lim ichidagi amallar (Arifmetika / Kasrlar / ...) ----------
function renderSection() {
  const sectionKey = state.selection.section;
  const section = (CONFIG.sections || []).find((s) => s.key === sectionKey) || { label: "Bo'lim" };
  const sectionDesc = {
    fractions: "Kasrlar ustida",
    percent: "Foizlar ustida",
  }[sectionKey] || "1–5 xonali sonlar ustida";
  const opKeys = Object.keys(CONFIG.operations).filter((k) => CONFIG.operations[k].section === sectionKey);
  const cards = opKeys.map((key) => {
    const op = CONFIG.operations[key];
    return `
      <div class="section-card" data-op="${key}" style="border-color:${op.color}22">
        <div class="icon-badge" style="background:${op.color}">${OP_EMOJI[key] || op.symbol}</div>
        <div class="title">${op.label}</div>
        <div class="desc">${sectionDesc}</div>
      </div>`;
  }).join("");

  appEl.innerHTML = `
    ${header(section.label, "Amal turini tanlang", true)}
    <div class="card-grid">${cards}</div>
  `;
  bindBack();
  document.querySelectorAll(".section-card").forEach((el) => {
    el.onclick = () => {
      state.selection.operation = el.dataset.op;
      pushScreen("digits");
    };
  });
}

// ---------- Xona / daraja tanlash ----------
function renderDigits() {
  const op = CONFIG.operations[state.selection.operation];
  const useLevelWording = op.section !== "arithmetic";
  const buttons = [];
  for (let d = CONFIG.min_digits; d <= CONFIG.max_digits; d++) {
    buttons.push(`<button class="choice-btn" data-d="${d}">${useLevelWording ? `${d}-daraja` : `${d} xonali`}</button>`);
  }
  appEl.innerHTML = `
    ${header(op.label, useLevelWording ? "Murakkablik darajasini tanlang" : "Sonlar xonasini tanlang", true)}
    <div class="choice-grid">${buttons.join("")}</div>
  `;
  bindBack();
  document.querySelectorAll(".choice-btn").forEach((el) => {
    el.onclick = () => {
      state.selection.digits = parseInt(el.dataset.d, 10);
      pushScreen("time");
    };
  });
}

// ---------- Vaqt tanlash ----------
function renderTime() {
  const op = CONFIG.operations[state.selection.operation];
  const buttons = CONFIG.time_options
    .map((t) => `<button class="choice-btn" data-s="${t.seconds}">${t.label}</button>`)
    .join("");
  appEl.innerHTML = `
    ${header(op.label, `${state.selection.digits} — har bir savol uchun vaqtni tanlang`, true)}
    <div class="choice-grid">${buttons}</div>
  `;
  bindBack();
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
  const t = state.test;
  const q = t.question;
  const pct = t.total_questions ? (t.progress.answered / t.total_questions) * 100 : 0;
  const correctPct = t.total_questions ? (t.progress.correct / t.total_questions) * 100 : 0;
  const wrongPct = t.total_questions ? (t.progress.wrong / t.total_questions) * 100 : 0;
  const instruction = QUESTION_INSTRUCTIONS[q.operation];
  const bigChoices = BIG_CHOICE_OPS.has(q.operation);
  const wordProblem = WORD_PROBLEM_OPS.has(q.operation);

  appEl.innerHTML = `
    <div class="test-topbar">
      <div class="progress-line">
        <span>${t.progress.answered} / ${t.total_questions} savol</span>
        <span><span class="stat-correct">✔ ${t.progress.correct}</span> &nbsp; <span class="stat-wrong">✘ ${t.progress.wrong}</span></span>
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
      ${q.choices.map((c, i) => `<button class="answer-btn${bigChoices ? " compare-btn" : ""}" data-c="${escapeHtml(c)}" data-i="${i}">${escapeHtml(c)}</button>`).join("")}
    </div>
    <button class="btn btn-danger-outline" id="btn-finish-test" style="margin-top:18px;">🏁 Testni tugatish</button>
  `;

  document.querySelectorAll(".answer-btn").forEach((el) => {
    el.onclick = () => onChooseAnswer(el.dataset.c);
  });
  document.getElementById("btn-finish-test").onclick = showFinishConfirmModal;
}

function showFinishConfirmModal() {
  const t = state.test;
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "finish-modal";
  modal.innerHTML = `
    <div class="modal-sheet">
      <h3>Testni yakunlaysizmi?</h3>
      <p>Hozirgacha ${t.progress.answered} / ${t.total_questions} savolga javob berdingiz. Qolgan savollar hisoblanmaydi.</p>
      <div class="btn-row">
        <button class="btn btn-outline" id="btn-finish-cancel">Davom etish</button>
        <button class="btn btn-danger-outline" id="btn-finish-confirm">🏁 Ha, tugatish</button>
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
    state.lastFeedback = null;
    state.screen = "test_result";
    render();
  } catch (e) {
    alert(e.message);
  }
}

function renderFeedbackBanner() {
  const fb = state.lastFeedback;
  if (fb.timedOut) {
    return `<div class="feedback-banner wrong">⏰ Vaqt tugadi — javob berolmadingiz. To'g'ri javob: ${dash(fb.correctAnswer)}</div>`;
  }
  if (fb.isCorrect) {
    return `<div class="feedback-banner correct">✅ To'g'ri!</div>`;
  }
  return `<div class="feedback-banner wrong">❌ Xato. Siz tanladingiz: ${dash(fb.chosen)}. To'g'ri javob: ${dash(fb.correctAnswer)}</div>`;
}

function onChooseAnswer(value) {
  state.pendingChoice = value;
  showConfirmModal();
}

function showConfirmModal() {
  const modal = document.createElement("div");
  modal.className = "modal-backdrop";
  modal.id = "confirm-modal";
  modal.innerHTML = `
    <div class="modal-sheet">
      <h3>Javobingiz: ${dash(state.pendingChoice)}</h3>
      <p>Tasdiqlaysizmi yoki qayta o'ylab ko'rasizmi?</p>
      <div class="btn-row">
        <button class="btn btn-outline" id="btn-rethink">🔄 Qayta o'ylash</button>
        <button class="btn btn-success" id="btn-confirm">✅ Tasdiqlash</button>
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

  const t = state.test;
  const q = t.question;
  const chosen = timedOut ? null : state.pendingChoice;
  const timeTaken = t.time_per_question * 1000 - Math.max(0, state.timer.deadline - Date.now());

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
    };

    t.progress = res.progress;

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
  const t = state.test;
  const total = t.total_questions;
  const answered = t.progress.answered;
  const correct = t.progress.correct;
  const wrong = t.progress.wrong;
  const early = answered < total;
  const good = answered > 0 && correct / answered >= 0.7;
  const summaryLine = early
    ? `${total} tadan <b>${answered}</b> tasiga javob berdingiz — shundan <b>${correct}</b> ta to'g'ri, <b>${wrong}</b> ta noto'g'ri`
    : `${total} tadan <b>${correct}</b> ta to'g'ri, <b>${wrong}</b> ta noto'g'ri`;
  appEl.innerHTML = `
    ${header("Test yakunlandi! 🎉")}
    <div class="feedback-banner ${good ? "correct" : "wrong"}" style="font-size:18px;padding:22px;">
      ${summaryLine}
    </div>
    <button class="btn btn-primary" id="btn-detail">Batafsil ko'rish</button>
    <div style="height:10px"></div>
    <button class="btn btn-outline" id="btn-home">Bosh menyu</button>
  `;
  document.getElementById("btn-detail").onclick = () => {
    state.viewAttemptId = t.attempt_id;
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
  appEl.innerHTML = `${header(isAdminView ? "Foydalanuvchi testlari" : "Natijalarim", null, true)}<div class="empty-state">Yuklanmoqda...</div>`;
  bindBack();
  try {
    const res = isAdminView
      ? await api(`/api/admin/users/${userId}/attempts`)
      : await api("/api/results");
    const attempts = res.attempts;
    const title = isAdminView
      ? `${res.user.last_name} ${res.user.first_name} testlari`
      : "Natijalarim";

    if (!attempts.length) {
      appEl.innerHTML = `${header(title, null, true)}<div class="empty-state">Hozircha testlar yo'q</div>`;
      bindBack();
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
            <div class="title">${op.label || a.operation}</div>
            <div class="date">${date}</div>
          </div>
          <div class="score ${scoreClass}">${a.correct_count}/${a.total_questions}</div>
        </div>`;
    }).join("");

    appEl.innerHTML = `${header(title, null, true)}<div>${rows}</div>`;
    bindBack();
    document.querySelectorAll(".result-row").forEach((el) => {
      el.onclick = () => {
        state.viewAttemptId = parseInt(el.dataset.id, 10);
        pushScreen("result_detail");
      };
    });
  } catch (e) {
    appEl.innerHTML = `${header("Xatolik", null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindBack();
  }
}

// ---------- Natija tafsiloti ----------
async function renderResultDetail() {
  appEl.innerHTML = `${header("Batafsil natija", null, true)}<div class="empty-state">Yuklanmoqda...</div>`;
  bindBack();
  try {
    const res = await api(`/api/results/${state.viewAttemptId}`);
    const a = res.attempt;
    const op = CONFIG.operations[a.operation] || {};
    const ownerLine = ME.is_admin && res.owner
      ? `<p class="subtitle">${res.owner.last_name} ${res.owner.first_name} ${res.owner.father_name}</p>`
      : "";

    const rows = res.questions.map((q) => {
      let statusClass = "wrong";
      let line;
      if (q.status === "pending") {
        statusClass = "";
        line = `<span class="ans-line">Javob berilmagan</span>`;
      } else if (q.status === "timeout") {
        line = `<span class="ans-line">⏰ Vaqt tugadi — <span class="correct-val">to'g'ri javob: ${dash(q.correct_answer)}</span></span>`;
      } else if (q.is_correct) {
        statusClass = "correct";
        line = `<span class="ans-line">Javobingiz: <span class="chosen-correct">${dash(q.selected_answer)}</span> ✔</span>`;
      } else {
        statusClass = "wrong";
        line = `<span class="ans-line">Javobingiz: <span class="chosen-wrong">${dash(q.selected_answer)}</span> — to'g'risi: <span class="correct-val">${dash(q.correct_answer)}</span></span>`;
      }
      return `
        <div class="detail-q-row ${statusClass}">
          <div class="expr">${q.order_index + 1}) ${questionExprHtml(q)}${questionSuffix(q)}</div>
          ${line}
        </div>`;
    }).join("");

    appEl.innerHTML = `
      ${header(op.label || a.operation, null, true)}
      ${ownerLine}
      <div class="feedback-banner correct" style="margin-bottom:16px;">
        ${a.total_questions} tadan <b>${a.correct_count}</b> to'g'ri, <b>${a.wrong_count}</b> noto'g'ri
      </div>
      ${rows}
    `;
    bindBack();
  } catch (e) {
    appEl.innerHTML = `${header("Xatolik", null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindBack();
  }
}

// ---------- Admin: foydalanuvchilar ----------
async function renderAdminUsers() {
  appEl.innerHTML = `${header("Admin panel", "Barcha foydalanuvchilar", true)}<div class="empty-state">Yuklanmoqda...</div>`;
  bindBack();
  try {
    const res = await api("/api/admin/users");
    if (!res.users.length) {
      appEl.innerHTML = `${header("Admin panel", "Barcha foydalanuvchilar", true)}<div class="empty-state">Hozircha foydalanuvchilar yo'q</div>`;
      bindBack();
      return;
    }
    const rows = res.users.map((u) => `
      <div class="admin-user-row" data-id="${u.telegram_id}">
        <div class="name">${u.last_name} ${u.first_name} ${u.father_name}${u.is_admin ? " 🛡" : ""}</div>
        <div class="sub">${u.username ? "@" + u.username : "username yo'q"} · ${u.attempts_count} ta test</div>
        <div class="stats"><span class="c">✔ ${u.total_correct}</span><span class="w">✘ ${u.total_wrong}</span></div>
      </div>`).join("");
    appEl.innerHTML = `${header("Admin panel", "Barcha foydalanuvchilar", true)}<div>${rows}</div>`;
    bindBack();
    document.querySelectorAll(".admin-user-row").forEach((el) => {
      el.onclick = () => {
        state.viewUserId = parseInt(el.dataset.id, 10);
        pushScreen("admin_attempts");
      };
    });
  } catch (e) {
    appEl.innerHTML = `${header("Xatolik", null, true)}<div class="empty-state">${escapeHtml(e.message)}</div>`;
    bindBack();
  }
}

init();
