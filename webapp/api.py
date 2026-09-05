"""REST API endpointlari (Flask blueprint)."""
import io

from flask import Blueprint, jsonify, request, send_file

from config import (
    BOT_USERNAME, MAX_DIGITS, MIN_DIGITS, OPERATIONS,
    QUESTIONS_PER_TEST, SECTIONS, SUPPORTED_LANGUAGES, TIME_OPTIONS,
)
from db import crud
from logic.question_generator import generate_test
from webapp.auth import AuthError, get_current_telegram_user
from webapp.logger import logger

api_bp = Blueprint("api", __name__, url_prefix="/api")


def err(status: int, detail: str):
    return jsonify({"detail": detail}), status


def current_user():
    """get_current_telegram_user() ni chaqiradi; xato bo'lsa AuthError ko'taradi."""
    return get_current_telegram_user()


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
        return err(400, "Tug'ilgan sana noto'g'ri")

    if not first_name or not last_name or not father_name:
        return err(400, "Ism, familiya va otasining ismini to'ldiring")
    if not (1900 <= birth_year <= 2100):
        return err(400, "Tug'ilgan yil noto'g'ri")
    if not (1 <= birth_month <= 12):
        return err(400, "Tug'ilgan oy noto'g'ri")
    if not (1 <= birth_day <= 31):
        return err(400, "Tug'ilgan kun noto'g'ri")

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
        return err(400, "Noto'g'ri til")

    user = crud.get_user(tg_user["id"])
    if not user:
        return err(400, "Avval ro'yxatdan o'ting")

    crud.set_user_language(tg_user["id"], language)
    logger.info("LANGUAGE_CHANGE user=%s til=%s", tg_user["id"], language)
    return jsonify({"ok": True, "language": language})


# ---------- Profil statistikasi: seriya, yutuqlar, mavzular, referral ----------

@api_bp.get("/stats")
def profile_stats():
    tg_user = current_user()
    user = crud.get_user(tg_user["id"])
    if not user:
        return err(400, "Avval ro'yxatdan o'ting")

    topics_raw = crud.topic_stats(tg_user["id"])
    by_section: dict = {}
    for row in topics_raw:
        section = OPERATIONS.get(row["operation"], {}).get("section", "other")
        agg = by_section.setdefault(section, {"total": 0, "correct": 0})
        agg["total"] += row["total"]
        agg["correct"] += row["correct"] or 0
    topic_stats = [
        {
            "section": section,
            "total": agg["total"],
            "correct": agg["correct"],
            "accuracy": round(100 * agg["correct"] / agg["total"]) if agg["total"] else 0,
        }
        for section, agg in by_section.items()
    ]

    rank_info = crud.user_rank(tg_user["id"])
    referral_code = user.get("referral_code") or ""
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}" if BOT_USERNAME else None

    return jsonify({
        "streak": {"current": user.get("current_streak") or 0, "longest": user.get("longest_streak") or 0},
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


@api_bp.get("/recommend")
def recommend_level():
    tg_user = current_user()
    operation = request.args.get("operation")
    if operation not in OPERATIONS:
        return err(400, "Noto'g'ri amal turi")

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
        return err(400, "Avval ro'yxatdan o'ting")

    body = request.get_json(silent=True) or {}
    operation = body.get("operation")
    try:
        digits = int(body.get("digits"))
        time_per_question = int(body.get("time_per_question"))
    except (TypeError, ValueError):
        return err(400, "Noto'g'ri parametrlar")

    if operation not in OPERATIONS:
        return err(400, "Noto'g'ri amal turi")
    if not (MIN_DIGITS <= digits <= MAX_DIGITS):
        return err(400, "Noto'g'ri xonalar soni")
    if not (5 <= time_per_question <= 3600):
        return err(400, "Noto'g'ri vaqt")

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


@api_bp.get("/tests/<int:attempt_id>/state")
def test_state(attempt_id: int):
    tg_user = current_user()
    attempt = crud.get_attempt(attempt_id)
    if not attempt or attempt["user_id"] != tg_user["id"]:
        return err(404, "Test topilmadi")
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
        return err(400, "Noto'g'ri savol ID")
    selected_answer = body.get("selected_answer")
    if selected_answer is not None:
        selected_answer = str(selected_answer)
    time_taken_ms = int(body.get("time_taken_ms") or 0)
    timed_out = bool(body.get("timed_out") or False)

    question = crud.get_question(question_id)
    if not question:
        return err(404, "Savol topilmadi")

    attempt = crud.get_attempt(question["attempt_id"])
    if not attempt or attempt["user_id"] != tg_user["id"]:
        return err(403, "Bu sizning testingiz emas")
    if question["status"] != "pending":
        return err(400, "Bu savolga allaqachon javob berilgan")

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
        return err(404, "Test topilmadi")

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
        return err(404, "Test topilmadi")
    if attempt["user_id"] != tg_user["id"] and not crud.is_admin(tg_user["id"]):
        return err(403, "Ruxsat yo'q")

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
        return err(403, "Faqat admin uchun")
    return jsonify({"users": crud.all_users_with_stats()})


@api_bp.get("/admin/users/<int:user_id>/attempts")
def admin_user_attempts(user_id: int):
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun")
    user = crud.get_user(user_id)
    if not user:
        return err(404, "Foydalanuvchi topilmadi")
    attempts = crud.list_user_attempts(user_id)
    return jsonify({"user": user, "attempts": [_attempt_summary(a) for a in attempts]})


@api_bp.get("/admin/export")
def admin_export():
    tg_user = current_user()
    if not _require_admin(tg_user):
        return err(403, "Faqat admin uchun")

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
