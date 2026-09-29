"""REST API endpointlari (Flask blueprint)."""
import datetime
import io

from flask import Blueprint, jsonify, request, send_file

from config import (
    BOT_USERNAME, MAX_DIGITS, MIN_DIGITS, OPERATIONS,
    QUESTIONS_PER_TEST, SECTIONS, SUPPORTED_LANGUAGES, TIME_OPTIONS,
)
from db import crud
from bot.telegram_api import send_message
from logic.certificate import generate_certificate_pdf
from logic.question_generator import generate_mixed_test, generate_review_test, generate_test
from webapp.auth import AuthError, get_current_telegram_user
from webapp.logger import logger

api_bp = Blueprint("api", __name__, url_prefix="/api")


def err(status: int, detail: str, code: str = None):
    return jsonify({"detail": detail, "code": code}), status


def current_user():
    """get_current_telegram_user() ni chaqiradi; xato bo'lsa AuthError ko'taradi."""
    return get_current_telegram_user()


def _valid_time_per_question(seconds: int) -> bool:
    """Har bir savol uchun ajratilgan vaqt to'g'ri qiymatmi?
    0 — 'vaqtsiz' (cheklovsiz) rejimini bildiradi."""
    return seconds == 0 or 5 <= seconds <= 3600


@api_bp.errorhandler(AuthError)
def handle_auth_error(e: AuthError):
    return err(e.status, e.message)


# ---------- Umumiy sozlamalar ----------

@api_bp.get("/config")
def get_config():
    return jsonify({
        "sections": SECTIONS,
        "operations": OPERATIONS,
        "time_options": TIME_OPTIONS,
        "min_digits": MIN_DIGITS,
        "max_digits": MAX_DIGITS,
        "questions_per_test": QUESTIONS_PER_TEST,
    })


# ---------- Foydalanuvchi / ro'yxatdan o'tish ----------

@api_bp.get("/me")
def get_me():
    tg_user = current_user()
    user = crud.get_user(tg_user["id"])
    return jsonify({
        "telegram_id": tg_user["id"],
        "registered": user is not None,
        "profile": user,
        "is_admin": crud.is_admin(tg_user["id"]),
    })


@api_bp.post("/register")
def register():
    tg_user = current_user()
    body = request.get_json(silent=True) or {}

    first_name = str(body.get("first_name", "")).strip()
    last_name = str(body.get("last_name", "")).strip()
    father_name = str(body.get("father_name", "")).strip()
    try:
        birth_year = int(body.get("birth_year"))
        birth_month = int(body.get("birth_month"))
        birth_day = int(body.get("birth_day"))
    except (TypeError, ValueError):
        return err(400, "Tug'ilgan sana noto'g'ri", "invalid_birthdate")

    if not first_name or not last_name or not father_name:
        return err(400, "Ism, familiya va otasining ismini to'ldiring", "missing_name_fields")
    if not (1900 <= birth_year <= 2100):
        return err(400, "Tug'ilgan yil noto'g'ri", "invalid_birth_year")
    if not (1 <= birth_month <= 12):
        return err(400, "Tug'ilgan oy noto'g'ri", "invalid_birth_month")
    if not (1 <= birth_day <= 31):
        return err(400, "Tug'ilgan kun noto'g'ri", "invalid_birth_day")

    language = body.get("language")
    if language not in SUPPORTED_LANGUAGES:
        language = None

    referred_by_id = None
    referrer_code = crud.consume_pending_referral(tg_user["id"])
    if referrer_code:
        referrer = crud.get_user_by_referral_code(referrer_code)
        if referrer and referrer["telegram_id"] != tg_user["id"]:
            referred_by_id = referrer["telegram_id"]

    user = crud.create_or_update_user(
        telegram_id=tg_user["id"],
        first_name=first_name,
        last_name=last_name,
        father_name=father_name,
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        username=tg_user.get("username"),
        language=language,
        referred_by_id=referred_by_id,
    )
    logger.info(
        "REGISTER user=%s (%s %s %s) tug'ilgan sana=%04d-%02d-%02d",
        tg_user["id"], last_name, first_name, father_name,
        birth_year, birth_month, birth_day,
    )
    return jsonify({"ok": True, "profile": user})


@api_bp.post("/language")
def set_language():
    """Ro'yxatdan o'tgan foydalanuvchi Mini App tilini xohlagan vaqtda
    o'zgartirishi uchun (yuqoridagi bayroqcha tugmasi orqali)."""
    tg_user = current_user()
    body = request.get_json(silent=True) or {}
    language = body.get("language")
    if language not in SUPPORTED_LANGUAGES:
        return err(400, "Noto'g'ri til", "invalid_language")

    user = crud.get_user(tg_user["id"])
    if not user:
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    crud.set_user_language(tg_user["id"], language)
    logger.info("LANGUAGE_CHANGE user=%s til=%s", tg_user["id"], language)
    return jsonify({"ok": True, "language": language})


# ---------- Profil statistikasi: seriya, yutuqlar, mavzular, referral ----------

CERTIFICATE_MIN_TOTAL = 40
CERTIFICATE_MIN_ACCURACY = 85


def _section_stats(telegram_id: int) -> list:
    topics_raw = crud.topic_stats(telegram_id)
    by_section: dict = {}
    for row in topics_raw:
        section = OPERATIONS.get(row["operation"], {}).get("section", "other")
        agg = by_section.setdefault(section, {"total": 0, "correct": 0})
        agg["total"] += row["total"]
        agg["correct"] += row["correct"] or 0
    return [
        {
            "section": section,
            "total": agg["total"],
            "correct": agg["correct"],
            "accuracy": round(100 * agg["correct"] / agg["total"]) if agg["total"] else 0,
        }
        for section, agg in by_section.items()
    ]


@api_bp.get("/stats")
def profile_stats():
    tg_user = current_user()
    user = crud.get_user(tg_user["id"])
    if not user:
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    topic_stats = _section_stats(tg_user["id"])
    for row in topic_stats:
        row["certificate_available"] = (
            row["total"] >= CERTIFICATE_MIN_TOTAL and row["accuracy"] >= CERTIFICATE_MIN_ACCURACY
        )

    rank_info = crud.user_rank(tg_user["id"])
    referral_code = user.get("referral_code") or ""
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}" if BOT_USERNAME else None

    return jsonify({
        "streak": crud.streak_status(tg_user["id"]),
        "achievements": crud.all_achievements_status(tg_user["id"]),
        "topic_stats": topic_stats,
        "rank": rank_info,
        "referral": {
            "code": referral_code,
            "link": referral_link,
            "count": crud.count_referrals(tg_user["id"]),
        },
    })


@api_bp.get("/leaderboard")
def get_leaderboard():
    tg_user = current_user()
    top = crud.leaderboard(10)
    return jsonify({
        "top": [
            {"first_name": r["first_name"], "last_name": r["last_name"], "points": r["points"]}
            for r in top
        ],
        "my_rank": crud.user_rank(tg_user["id"]),
    })


@api_bp.get("/certificate/<section_key>")
def get_certificate(section_key: str):
    """Foydalanuvchi biror bo'lim bo'yicha yetarlicha savolga (>=40) yuqori
    aniqlik bilan (>=85%) javob bergan bo'lsa, PDF sertifikat qaytaradi."""
    tg_user = current_user()
    user = crud.get_user(tg_user["id"])
    if not user:
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    section_meta = next((s for s in SECTIONS if s["key"] == section_key), None)
    if not section_meta:
        return err(400, "Noto'g'ri bo'lim", "invalid_section")

    stats = next((r for r in _section_stats(tg_user["id"]) if r["section"] == section_key), None)
    if not stats or stats["total"] < CERTIFICATE_MIN_TOTAL or stats["accuracy"] < CERTIFICATE_MIN_ACCURACY:
        return err(400, "Sertifikat uchun hali yetarli natija yo'q", "certificate_not_available")

    full_name = f"{user['first_name']} {user['last_name']}"
    date_str = datetime.date.today().isoformat()
    pdf_bytes = generate_certificate_pdf(
        full_name=full_name,
        section_label=section_meta["label"],
        accuracy=stats["accuracy"],
        total=stats["total"],
        date_str=date_str,
    )
    logger.info("CERTIFICATE user=%s section=%s aniqlik=%s%%", tg_user["id"], section_key, stats["accuracy"])
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"mathbot_sertifikat_{section_key}.pdf",
    )


@api_bp.get("/recommend")
def recommend_level():
    tg_user = current_user()
    operation = request.args.get("operation")
    if operation not in OPERATIONS:
        return err(400, "Noto'g'ri amal turi", "invalid_operation")

    last = crud.last_attempt_for_operation(tg_user["id"], operation)
    if not last or not last["total_questions"]:
        return jsonify({"suggested_level": None})

    ratio = last["correct_count"] / last["total_questions"]
    level = last["digits"]
    if ratio >= 0.85 and level < MAX_DIGITS:
        suggested = level + 1
    elif ratio < 0.5 and level > MIN_DIGITS:
        suggested = level - 1
    else:
        suggested = level
    return jsonify({"suggested_level": suggested, "last_level": level, "last_accuracy": round(ratio * 100)})


# ---------- Test topshirish ----------

def _require_registered(telegram_id: int):
    user = crud.get_user(telegram_id)
    if not user:
        return None
    return user


def _on_test_finished(telegram_id: int, counts: dict, total_questions: int) -> dict:
    """Test yakunlanganda (to'liq yoki erta) seriya va yutuqlarni yangilaydi.
    Javobga qo'shiladigan {"streak":..., "new_achievements":[...]} qaytaradi."""
    streak = crud.update_streak_on_finish(telegram_id)
    attempts_count = crud.user_stats(telegram_id)["attempts_count"]
    perfect = total_questions > 0 and counts["correct"] == total_questions
    new_achievements = crud.award_achievements(
        telegram_id, current_streak=streak["current"],
        perfect_score=perfect, attempts_count=attempts_count,
    )
    return {"streak": streak, "new_achievements": new_achievements}


def _public_question(q: dict) -> dict:
    """Foydalanuvchiga to'g'ri javobni oshkor qilmasdan savolni qaytaradi."""
    return {
        "id": q["id"],
        "order_index": q["order_index"],
        "a": q["operand_a"],
        "b": q["operand_b"],
        "c": q.get("operand_c"),
        "d": q.get("operand_d"),
        "operation": q["operation"],
        "choices": q["choices"],
        "display_text": q.get("display_text"),
        "extra": q.get("extra"),
    }


@api_bp.post("/tests/start")
def start_test():
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    body = request.get_json(silent=True) or {}
    operation = body.get("operation")
    try:
        digits = int(body.get("digits"))
        time_per_question = int(body.get("time_per_question"))
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri parametrlar", "invalid_params")

    if operation not in OPERATIONS:
        return err(400, "Noto'g'ri amal turi", "invalid_operation")
    if not (MIN_DIGITS <= digits <= MAX_DIGITS):
        return err(400, "Noto'g'ri xonalar soni", "invalid_digits")
    if not _valid_time_per_question(time_per_question):
        return err(400, "Noto'g'ri vaqt", "invalid_time")

    questions = generate_test(operation, digits, QUESTIONS_PER_TEST)
    attempt_id = crud.create_attempt(
        user_id=tg_user["id"],
        operation=operation,
        digits=digits,
        time_per_q=time_per_question,
        total_questions=QUESTIONS_PER_TEST,
    )
    crud.add_questions(attempt_id, questions)
    logger.info(
        "TEST_START user=%s attempt=%s amal=%s xona=%s vaqt=%ss",
        tg_user["id"], attempt_id, operation, digits, time_per_question,
    )

    first_q = crud.get_next_pending_question(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        "total_questions": QUESTIONS_PER_TEST,
        "time_per_question": time_per_question,
        "question": _public_question(first_q) if first_q else None,
        "progress": {"answered": 0, "correct": 0, "wrong": 0},
    })


@api_bp.post("/tests/start-mixed")
def start_mixed_test():
    """Aralash/DTM uslubidagi imtihon: turli mavzu va qiyinlikdagi savollar
    bitta test ichida aralashtirilgan holda beriladi."""
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    body = request.get_json(silent=True) or {}
    try:
        time_per_question = int(body.get("time_per_question"))
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri parametrlar", "invalid_params")
    if not _valid_time_per_question(time_per_question):
        return err(400, "Noto'g'ri vaqt", "invalid_time")

    questions = generate_mixed_test(QUESTIONS_PER_TEST)
    attempt_id = crud.create_attempt(
        user_id=tg_user["id"],
        operation="mixed_exam",
        digits=0,
        time_per_q=time_per_question,
        total_questions=QUESTIONS_PER_TEST,
    )
    crud.add_questions(attempt_id, questions)
    logger.info(
        "MIXED_TEST_START user=%s attempt=%s vaqt=%ss",
        tg_user["id"], attempt_id, time_per_question,
    )

    first_q = crud.get_next_pending_question(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        "total_questions": QUESTIONS_PER_TEST,
        "time_per_question": time_per_question,
        "question": _public_question(first_q) if first_q else None,
        "progress": {"answered": 0, "correct": 0, "wrong": 0},
    })


@api_bp.get("/tests/mistakes/available")
def mistakes_available():
    """Frontendga 'Xatolarni qayta ko'rish' tugmasini ko'rsatish/yashirish
    uchun — yetarlicha xato javob tarixi bor-yo'qligini bildiradi."""
    tg_user = current_user()
    weak = crud.weak_operations(tg_user["id"], limit=12)
    total_wrong = sum(w["wrong_count"] for w in weak)
    return jsonify({"available": total_wrong >= 5, "topics_count": len(weak)})


@api_bp.post("/tests/start-review")
def start_review_test():
    """'Xatolarni qayta ko'rish' — foydalanuvchi eng ko'p xato qilgan
    mavzulardan (og'irlik bilan) yangi savollar bilan test tuzadi."""
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    body = request.get_json(silent=True) or {}
    try:
        time_per_question = int(body.get("time_per_question"))
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri parametrlar", "invalid_params")
    if not _valid_time_per_question(time_per_question):
        return err(400, "Noto'g'ri vaqt", "invalid_time")

    weak = crud.weak_operations(tg_user["id"], limit=12)
    if not weak or sum(w["wrong_count"] for w in weak) < 5:
        return err(400, "Hali xatolar tarixi yetarli emas", "not_enough_mistakes")

    total_questions = min(QUESTIONS_PER_TEST, max(10, sum(w["wrong_count"] for w in weak)))
    questions = generate_review_test(weak, total_questions)
    attempt_id = crud.create_attempt(
        user_id=tg_user["id"],
        operation="mistake_review",
        digits=0,
        time_per_q=time_per_question,
        total_questions=len(questions),
    )
    crud.add_questions(attempt_id, questions)
    logger.info(
        "REVIEW_TEST_START user=%s attempt=%s mavzular=%s vaqt=%ss",
        tg_user["id"], attempt_id, [w["operation"] for w in weak], time_per_question,
    )

    first_q = crud.get_next_pending_question(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        "total_questions": len(questions),
        "time_per_question": time_per_question,
        "question": _public_question(first_q) if first_q else None,
        "progress": {"answered": 0, "correct": 0, "wrong": 0},
    })


@api_bp.get("/tests/<int:attempt_id>/state")
def test_state(attempt_id: int):
    tg_user = current_user()
    attempt = crud.get_attempt(attempt_id)
    if not attempt or attempt["user_id"] != tg_user["id"]:
        return err(404, "Test topilmadi", "test_not_found")
    next_q = crud.get_next_pending_question(attempt_id)
    counts = crud.update_attempt_counts(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        "total_questions": attempt["total_questions"],
        "time_per_question": attempt["time_per_q"],
        "question": _public_question(next_q) if next_q else None,
        "progress": {
            "answered": counts["correct"] + counts["wrong"],
            "correct": counts["correct"],
            "wrong": counts["wrong"],
        },
        "finished": next_q is None,
    })


@api_bp.post("/tests/answer")
def submit_answer():
    tg_user = current_user()
    body = request.get_json(silent=True) or {}

    try:
        question_id = int(body.get("question_id"))
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri savol ID", "invalid_question_id")
    selected_answer = body.get("selected_answer")
    if selected_answer is not None:
        selected_answer = str(selected_answer)
    time_taken_ms = int(body.get("time_taken_ms") or 0)
    timed_out = bool(body.get("timed_out") or False)

    question = crud.get_question(question_id)
    if not question:
        return err(404, "Savol topilmadi", "question_not_found")

    attempt = crud.get_attempt(question["attempt_id"])
    if not attempt or attempt["user_id"] != tg_user["id"]:
        return err(403, "Bu sizning testingiz emas", "not_your_test")
    if question["status"] != "pending":
        return err(400, "Bu savolga allaqachon javob berilgan", "already_answered")

    is_correct = (not timed_out) and selected_answer == question["correct_answer"]
    crud.answer_question(
        question_id=question_id,
        selected_answer=selected_answer,
        is_correct=is_correct,
        time_taken_ms=time_taken_ms,
        timed_out=timed_out,
    )
    logger.info(
        "ANSWER user=%s attempt=%s savol=%s tanlandi=%s to'g'ri_javob=%s natija=%s vaqt_tugadi=%s",
        tg_user["id"], attempt["id"], question_id, selected_answer,
        question["correct_answer"], "TO'G'RI" if is_correct else "XATO", timed_out,
    )

    next_q = crud.get_next_pending_question(attempt["id"])
    counts = crud.update_attempt_counts(attempt["id"])
    finished = next_q is None
    finish_info = {"streak": None, "new_achievements": []}
    if finished:
        crud.finish_attempt(attempt["id"])
        logger.info(
            "TEST_FINISH user=%s attempt=%s to'g'ri=%s xato=%s",
            tg_user["id"], attempt["id"], counts["correct"], counts["wrong"],
        )
        finish_info = _on_test_finished(tg_user["id"], counts, attempt["total_questions"])

    return jsonify({
        "is_correct": is_correct,
        "correct_answer": question["correct_answer"],
        "next_question": _public_question(next_q) if next_q else None,
        "progress": {
            "answered": counts["correct"] + counts["wrong"],
            "correct": counts["correct"],
            "wrong": counts["wrong"],
        },
        "finished": finished,
        "streak": finish_info["streak"],
        "new_achievements": finish_info["new_achievements"],
    })


@api_bp.post("/tests/<int:attempt_id>/finish")
def finish_test_early(attempt_id: int):
    """Foydalanuvchi hali barcha savollarga javob bermay turib testni
    to'xtatmoqchi bo'lsa chaqiriladi. Javobsiz qolgan savollar shunchaki
    'pending' holatida qoladi (hisobga olinmaydi)."""
    tg_user = current_user()
    attempt = crud.get_attempt(attempt_id)
    if not attempt or attempt["user_id"] != tg_user["id"]:
        return err(404, "Test topilmadi", "test_not_found")

    finish_info = {"streak": None, "new_achievements": []}
    if attempt["status"] == "finished":
        counts = {"correct": attempt["correct_count"], "wrong": attempt["wrong_count"]}
    else:
        counts = crud.finish_attempt(attempt_id)
        logger.info(
            "TEST_FINISH_EARLY user=%s attempt=%s to'g'ri=%s xato=%s",
            tg_user["id"], attempt_id, counts["correct"], counts["wrong"],
        )
        finish_info = _on_test_finished(tg_user["id"], counts, attempt["total_questions"])

    return jsonify({
        "ok": True,
        "progress": {
            "answered": counts["correct"] + counts["wrong"],
            "correct": counts["correct"],
            "wrong": counts["wrong"],
        },
        "streak": finish_info["streak"],
        "new_achievements": finish_info["new_achievements"],
    })


# ---------- Natijalar ----------

def _attempt_summary(a: dict) -> dict:
    op = OPERATIONS.get(a["operation"], {})
    return {
        "id": a["id"],
        "operation": a["operation"],
        "operation_label": op.get("label", a["operation"]),
        "digits": a["digits"],
        "time_per_q": a["time_per_q"],
        "total_questions": a["total_questions"],
        "correct_count": a["correct_count"],
        "wrong_count": a["wrong_count"],
        "status": a["status"],
        "started_at": a["started_at"],
        "finished_at": a["finished_at"],
    }


@api_bp.get("/results")
def my_results():
    tg_user = current_user()
    attempts = crud.list_user_attempts(tg_user["id"])
    return jsonify({"attempts": [_attempt_summary(a) for a in attempts]})


@api_bp.get("/results/<int:attempt_id>")
def result_detail(attempt_id: int):
    tg_user = current_user()
    attempt = crud.get_attempt(attempt_id)
    if not attempt:
        return err(404, "Test topilmadi", "test_not_found")
    if attempt["user_id"] != tg_user["id"] and not crud.is_admin(tg_user["id"]):
        return err(403, "Ruxsat yo'q", "access_denied")

    owner = crud.get_user(attempt["user_id"])
    questions = crud.get_attempt_questions(attempt_id)
    return jsonify({
        "attempt": _attempt_summary(attempt),
        "owner": owner,
        "questions": [
            {
                "order_index": q["order_index"],
                "a": q["operand_a"],
                "b": q["operand_b"],
                "c": q.get("operand_c"),
                "d": q.get("operand_d"),
                "operation": q["operation"],
                "choices": q["choices"],
                "display_text": q.get("display_text"),
                "extra": q.get("extra"),
                "correct_answer": q["correct_answer"],
                "selected_answer": q["selected_answer"],
                "is_correct": bool(q["is_correct"]) if q["is_correct"] is not None else None,
                "status": q["status"],
                "time_taken_ms": q["time_taken_ms"],
            }
            for q in questions
        ],
    })


# ---------- Admin ----------

def _require_admin(tg_user: dict):
    return crud.is_admin(tg_user["id"])


@api_bp.get("/admin/users")
def admin_users():
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun", "admin_only")
    return jsonify({"users": crud.all_users_with_stats()})


@api_bp.get("/admin/users/<int:user_id>/attempts")
def admin_user_attempts(user_id: int):
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun", "admin_only")
    user = crud.get_user(user_id)
    if not user:
        return err(404, "Foydalanuvchi topilmadi", "user_not_found")
    attempts = crud.list_user_attempts(user_id)
    return jsonify({"user": user, "attempts": [_attempt_summary(a) for a in attempts]})


@api_bp.get("/admin/export")
def admin_export():
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun", "admin_only")

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Foydalanuvchilar"
    headers = [
        "Telegram ID", "Familiya", "Ism", "Otasining ismi", "Username",
        "Ro'yxatdan o'tgan sana", "Testlar soni", "To'g'ri javoblar",
        "Xato javoblar", "Joriy seriya", "Eng uzun seriya", "Til",
    ]
    ws.append(headers)
    for u in crud.all_users_with_stats():
        ws.append([
            u["telegram_id"], u["last_name"], u["first_name"], u["father_name"],
            u["username"] or "", u["registered_at"], u["attempts_count"],
            u["total_correct"], u["total_wrong"], u["current_streak"] or 0,
            u["longest_streak"] or 0, u.get("language") or "uz",
        ])
    for i, _ in enumerate(headers, start=1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    logger.info("ADMIN_EXPORT admin=%s", tg_user["id"])
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="mathbot_foydalanuvchilar.xlsx",
    )


@api_bp.get("/admin/analytics")
def admin_analytics():
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun", "admin_only")
    return jsonify(crud.admin_analytics(days=7))


MAX_BROADCAST_LEN = 3500  # Telegram xabar limiti (4096) dan xavfsiz zaxira bilan kamroq


# ---------- Guruh/sinf va uy vazifasi ----------

MAX_GROUP_NAME_LEN = 60


def _group_summary(g: dict) -> dict:
    return {
        "id": g["id"],
        "name": g["name"],
        "join_code": g["join_code"],
        "owner_id": g["owner_id"],
        "member_count": g.get("member_count", 1),
        "is_owner": bool(g.get("is_owner")),
        "created_at": g.get("created_at"),
    }


@api_bp.get("/groups")
def list_my_groups():
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")
    groups = crud.user_groups(tg_user["id"])
    return jsonify({"groups": [_group_summary(g) for g in groups]})


@api_bp.post("/groups")
def create_group():
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")
    body = request.get_json(silent=True) or {}
    name = str(body.get("name", "")).strip()
    if not name:
        return err(400, "Guruh nomini kiriting", "missing_group_name")
    if len(name) > MAX_GROUP_NAME_LEN:
        return err(400, "Guruh nomi juda uzun", "group_name_too_long")

    group = crud.create_group(name, tg_user["id"])
    logger.info("GROUP_CREATE owner=%s group=%s kod=%s", tg_user["id"], group["id"], group["join_code"])
    group["is_owner"] = True
    group["member_count"] = 1
    return jsonify({"ok": True, "group": _group_summary(group)})


@api_bp.post("/groups/join")
def join_group():
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")
    body = request.get_json(silent=True) or {}
    join_code = str(body.get("join_code", "")).strip()
    if not join_code:
        return err(400, "Qo'shilish kodini kiriting", "missing_join_code")

    group = crud.join_group(join_code, tg_user["id"])
    if not group:
        return err(404, "Bunday kod bilan guruh topilmadi", "group_not_found")
    logger.info("GROUP_JOIN user=%s group=%s", tg_user["id"], group["id"])
    return jsonify({"ok": True, "group_id": group["id"], "group_name": group["name"]})


@api_bp.get("/groups/<int:group_id>")
def group_detail(group_id: int):
    tg_user = current_user()
    group = crud.get_group(group_id)
    if not group or not crud.is_group_member(group_id, tg_user["id"]):
        return err(404, "Guruh topilmadi", "group_not_found")

    is_owner = group["owner_id"] == tg_user["id"]
    members = crud.group_members(group_id)
    homework_list = crud.list_homework(group_id)
    hw_out = []
    for hw in homework_list:
        item = {
            "id": hw["id"], "operation": hw["operation"], "digits": hw["digits"],
            "question_count": hw["question_count"], "time_per_q": hw["time_per_q"],
            "created_at": hw["created_at"], "due_at": hw["due_at"],
        }
        if is_owner:
            item["completion"] = crud.homework_completion(hw["id"], group_id)
        else:
            status = crud.homework_status_for_user(hw["id"], tg_user["id"])
            item["my_status"] = {
                "completed": status is not None,
                "correct_count": status["correct_count"] if status else None,
                "total_questions": status["total_questions"] if status else None,
            }
        hw_out.append(item)

    return jsonify({
        "group": {
            "id": group["id"], "name": group["name"], "join_code": group["join_code"],
            "is_owner": is_owner, "owner_id": group["owner_id"],
        },
        "members": members,
        "homework": hw_out,
    })


@api_bp.post("/groups/<int:group_id>/homework")
def create_group_homework(group_id: int):
    tg_user = current_user()
    group = crud.get_group(group_id)
    if not group or not crud.is_group_member(group_id, tg_user["id"]):
        return err(404, "Guruh topilmadi", "group_not_found")
    if group["owner_id"] != tg_user["id"]:
        return err(403, "Faqat guruh egasi uy vazifasi bera oladi", "not_group_owner")

    body = request.get_json(silent=True) or {}
    operation = body.get("operation")
    try:
        digits = int(body.get("digits"))
        time_per_question = int(body.get("time_per_question"))
        question_count = int(body.get("question_count") or QUESTIONS_PER_TEST)
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri parametrlar", "invalid_params")

    if operation not in OPERATIONS:
        return err(400, "Noto'g'ri amal turi", "invalid_operation")
    if not (MIN_DIGITS <= digits <= MAX_DIGITS):
        return err(400, "Noto'g'ri xonalar soni", "invalid_digits")
    if not _valid_time_per_question(time_per_question):
        return err(400, "Noto'g'ri vaqt", "invalid_time")
    if not (5 <= question_count <= 50):
        return err(400, "Savollar soni noto'g'ri", "invalid_question_count")

    due_at = body.get("due_at") or None
    hw_id = crud.create_homework(
        group_id=group_id, operation=operation, digits=digits,
        question_count=question_count, time_per_q=time_per_question,
        created_by=tg_user["id"], due_at=due_at,
    )
    logger.info("HOMEWORK_CREATE group=%s hw=%s amal=%s", group_id, hw_id, operation)
    return jsonify({"ok": True, "homework_id": hw_id})


@api_bp.post("/homework/<int:homework_id>/start")
def start_homework(homework_id: int):
    tg_user = current_user()
    hw = crud.get_homework(homework_id)
    if not hw or not crud.is_group_member(hw["group_id"], tg_user["id"]):
        return err(404, "Uy vazifasi topilmadi", "homework_not_found")

    questions = generate_test(hw["operation"], hw["digits"], hw["question_count"])
    attempt_id = crud.create_attempt(
        user_id=tg_user["id"], operation=hw["operation"], digits=hw["digits"],
        time_per_q=hw["time_per_q"], total_questions=hw["question_count"],
        homework_id=homework_id,
    )
    crud.add_questions(attempt_id, questions)
    logger.info("HOMEWORK_START user=%s hw=%s attempt=%s", tg_user["id"], homework_id, attempt_id)

    first_q = crud.get_next_pending_question(attempt_id)
    return jsonify({
        "attempt_id": attempt_id,
        "total_questions": hw["question_count"],
        "time_per_question": hw["time_per_q"],
        "question": _public_question(first_q) if first_q else None,
        "progress": {"answered": 0, "correct": 0, "wrong": 0},
    })


@api_bp.post("/duels")
def create_duel_endpoint():
    """Do'stni chaqirish — QAT'IY savollar to'plami bilan duel yaratadi va
    yaratuvchining o'zi ham darhol o'ynashni boshlaydi. (Haqiqiy real-vaqtli
    multiplayer o'rniga asinxron duel — PythonAnywhere webhook-asosidagi
    bepul hostingda doimiy WebSocket ulanishi yo'qligi sababli.)"""
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    body = request.get_json(silent=True) or {}
    operation = body.get("operation")
    try:
        digits = int(body.get("digits"))
        time_per_question = int(body.get("time_per_question"))
        question_count = int(body.get("question_count") or QUESTIONS_PER_TEST)
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri parametrlar", "invalid_params")

    if operation not in OPERATIONS:
        return err(400, "Noto'g'ri amal turi", "invalid_operation")
    if not (MIN_DIGITS <= digits <= MAX_DIGITS):
        return err(400, "Noto'g'ri xonalar soni", "invalid_digits")
    if not _valid_time_per_question(time_per_question):
        return err(400, "Noto'g'ri vaqt", "invalid_time")
    if not (5 <= question_count <= 50):
        return err(400, "Savollar soni noto'g'ri", "invalid_question_count")

    questions = generate_test(operation, digits, question_count)
    duel = crud.create_duel(
        creator_id=tg_user["id"], operation=operation, digits=digits,
        question_count=question_count, time_per_q=time_per_question, questions=questions,
    )
    logger.info("DUEL_CREATE creator=%s duel=%s kod=%s", tg_user["id"], duel["id"], duel["join_code"])

    first_q = crud.get_next_pending_question(duel["creator_attempt_id"])
    return jsonify({
        "duel_id": duel["id"],
        "join_code": duel["join_code"],
        "attempt_id": duel["creator_attempt_id"],
        "total_questions": question_count,
        "time_per_question": time_per_question,
        "question": _public_question(first_q) if first_q else None,
        "progress": {"answered": 0, "correct": 0, "wrong": 0},
    })


@api_bp.post("/duels/join")
def join_duel_endpoint():
    tg_user = current_user()
    if not _require_registered(tg_user["id"]):
        return err(400, "Avval ro'yxatdan o'ting", "not_registered")

    body = request.get_json(silent=True) or {}
    join_code = str(body.get("join_code", "")).strip()
    if not join_code:
        return err(400, "Qo'shilish kodini kiriting", "missing_join_code")

    result = crud.join_duel(join_code, tg_user["id"])
    if result is None:
        return err(404, "Bunday kod bilan duel topilmadi", "duel_not_found")
    if result.get("error") == "own_duel":
        return err(400, "O'zingiz yaratgan duelga qo'shila olmaysiz", "duel_own")
    if result.get("error") == "already_taken":
        return err(400, "Bu duelga boshqa raqib allaqachon qo'shilgan", "duel_already_taken")

    attempt_id = result["opponent_attempt_id"]
    logger.info("DUEL_JOIN opponent=%s duel=%s", tg_user["id"], result["id"])
    first_q = crud.get_next_pending_question(attempt_id)
    return jsonify({
        "duel_id": result["id"],
        "attempt_id": attempt_id,
        "total_questions": result["question_count"],
        "time_per_question": result["time_per_q"],
        "question": _public_question(first_q) if first_q else None,
        "progress": {"answered": 0, "correct": 0, "wrong": 0},
    })


@api_bp.get("/duels/<int:duel_id>")
def duel_detail(duel_id: int):
    tg_user = current_user()
    result = crud.duel_result(duel_id, tg_user["id"])
    if not result:
        return err(404, "Duel topilmadi", "duel_not_found")
    return jsonify(result)


@api_bp.post("/admin/broadcast")
def admin_broadcast():
    """Barcha ro'yxatdan o'tgan foydalanuvchilarga bitta xabar yuboradi
    (admin-only). Har bir foydalanuvchiga alohida so'rov ketadi, shu
    sabab ko'p foydalanuvchida bu biroz vaqt olishi mumkin."""
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun", "admin_only")

    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    if not message:
        return err(400, "Xabar matni bo'sh bo'lmasligi kerak", "empty_broadcast_message")
    if len(message) > MAX_BROADCAST_LEN:
        return err(400, "Xabar juda uzun", "broadcast_message_too_long")

    users = crud.all_users_with_stats()
    sent, failed = 0, 0
    for u in users:
        try:
            send_message(u["telegram_id"], message)
            sent += 1
        except Exception:
            failed += 1
            logger.exception("BROADCAST xatolik: user=%s", u["telegram_id"])

    logger.info("BROADCAST admin=%s yuborildi=%s xato=%s jami=%s", tg_user["id"], sent, failed, len(users))
    return jsonify({"ok": True, "sent": sent, "failed": failed, "total": len(users)})
