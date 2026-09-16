"""Ma'lumotlar bazasi bilan ishlash funksiyalari (CRUD)."""
import datetime
import json
import random
import string
from typing import Optional

from config import ACHIEVEMENTS, ADMIN_IDS
from db.database import db_cursor, get_db


def _today_str() -> str:
    return datetime.datetime.utcnow().date().isoformat()


# ---------- USERS ----------

def get_user(telegram_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    return dict(row) if row else None


def create_or_update_user(
    telegram_id: int,
    first_name: str,
    last_name: str,
    father_name: str,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    username: Optional[str] = None,
    language: Optional[str] = None,
    referred_by_id: Optional[int] = None,
) -> dict:
    is_admin = 1 if telegram_id in ADMIN_IDS else 0
    with db_cursor() as cur:
        existing = get_user(telegram_id)
        if existing:
            if language:
                cur.execute(
                    """UPDATE users SET first_name=?, last_name=?, father_name=?,
                       birth_year=?, birth_month=?, birth_day=?, username=?, is_admin=?,
                       language=?
                       WHERE telegram_id=?""",
                    (first_name, last_name, father_name, birth_year, birth_month,
                     birth_day, username, is_admin, language, telegram_id),
                )
            else:
                cur.execute(
                    """UPDATE users SET first_name=?, last_name=?, father_name=?,
                       birth_year=?, birth_month=?, birth_day=?, username=?, is_admin=?
                       WHERE telegram_id=?""",
                    (first_name, last_name, father_name, birth_year, birth_month,
                     birth_day, username, is_admin, telegram_id),
                )
        else:
            referral_code = format(telegram_id, "X")
            cur.execute(
                """INSERT INTO users
                   (telegram_id, first_name, last_name, father_name,
                    birth_year, birth_month, birth_day, username, is_admin, language,
                    referral_code, referred_by_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (telegram_id, first_name, last_name, father_name, birth_year,
                 birth_month, birth_day, username, is_admin, language or "uz",
                 referral_code, referred_by_id),
            )
    return get_user(telegram_id)


def get_user_by_referral_code(code: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE referral_code = ?", (code.upper(),)
    ).fetchone()
    return dict(row) if row else None


def count_referrals(telegram_id: int) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM users WHERE referred_by_id = ?", (telegram_id,)
    ).fetchone()
    return row["n"] or 0


def record_pending_referral(telegram_id: int, referrer_code: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO pending_referrals (telegram_id, referrer_code)
               VALUES (?, ?)
               ON CONFLICT(telegram_id) DO UPDATE SET referrer_code=excluded.referrer_code""",
            (telegram_id, referrer_code.upper()),
        )


def consume_pending_referral(telegram_id: int) -> Optional[str]:
    conn = get_db()
    row = conn.execute(
        "SELECT referrer_code FROM pending_referrals WHERE telegram_id=?",
        (telegram_id,),
    ).fetchone()
    if not row:
        return None
    with db_cursor() as cur:
        cur.execute("DELETE FROM pending_referrals WHERE telegram_id=?", (telegram_id,))
    return row["referrer_code"]


def set_user_language(telegram_id: int, language: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET language=? WHERE telegram_id=?",
            (language, telegram_id),
        )


def is_admin(telegram_id: int) -> bool:
    user = get_user(telegram_id)
    if user and user["is_admin"]:
        return True
    return telegram_id in ADMIN_IDS


def list_all_users() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM users ORDER BY registered_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


# ---------- ATTEMPTS ----------

def create_attempt(user_id: int, operation: str, digits: int,
                    time_per_q: int, total_questions: int,
                    homework_id: Optional[int] = None,
                    duel_id: Optional[int] = None) -> int:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO attempts
               (user_id, operation, digits, time_per_q, total_questions, homework_id, duel_id)
               VALUES (?,?,?,?,?,?,?)""",
            (user_id, operation, digits, time_per_q, total_questions, homework_id, duel_id),
        )
        return cur.lastrowid


def add_questions(attempt_id: int, questions: list[dict]) -> None:
    with db_cursor() as cur:
        for idx, q in enumerate(questions):
            extra = q.get("extra")
            cur.execute(
                """INSERT INTO questions
                   (attempt_id, order_index, operand_a, operand_b, operand_c,
                    operand_d, operation, correct_answer, choices, display_text,
                    extra_data)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (attempt_id, idx, q["a"], q["b"], q.get("c"), q.get("d"),
                 q["operation"], q["answer"], json.dumps(q["choices"]),
                 q.get("display_text"),
                 json.dumps(extra) if extra is not None else None),
            )


def get_attempt(attempt_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
    ).fetchone()
    return dict(row) if row else None


def _parse_question_row(d: dict) -> dict:
    d["choices"] = json.loads(d["choices"])
    d["extra"] = json.loads(d["extra_data"]) if d.get("extra_data") else None
    return d


def get_attempt_questions(attempt_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM questions WHERE attempt_id = ? ORDER BY order_index",
        (attempt_id,),
    ).fetchall()
    return [_parse_question_row(dict(r)) for r in rows]


def get_question(question_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM questions WHERE id = ?", (question_id,)
    ).fetchone()
    if not row:
        return None
    return _parse_question_row(dict(row))


def get_next_pending_question(attempt_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        """SELECT * FROM questions WHERE attempt_id = ? AND status = 'pending'
           ORDER BY order_index LIMIT 1""",
        (attempt_id,),
    ).fetchone()
    if not row:
        return None
    return _parse_question_row(dict(row))


def answer_question(question_id: int, selected_answer: Optional[int],
                     is_correct: bool, time_taken_ms: int,
                     timed_out: bool = False) -> None:
    status = "timeout" if timed_out else "answered"
    with db_cursor() as cur:
        cur.execute(
            """UPDATE questions SET selected_answer=?, is_correct=?, status=?,
               time_taken_ms=?, answered_at=datetime('now') WHERE id=?""",
            (selected_answer, 1 if is_correct else 0, status,
             time_taken_ms, question_id),
        )


def update_attempt_counts(attempt_id: int) -> dict:
    conn = get_db()
    row = conn.execute(
        """SELECT
             SUM(CASE WHEN is_correct=1 THEN 1 ELSE 0 END) AS correct,
             SUM(CASE WHEN is_correct=0 THEN 1 ELSE 0 END) AS wrong
           FROM questions WHERE attempt_id=?""",
        (attempt_id,),
    ).fetchone()
    correct = row["correct"] or 0
    wrong = row["wrong"] or 0
    with db_cursor() as cur:
        cur.execute(
            "UPDATE attempts SET correct_count=?, wrong_count=? WHERE id=?",
            (correct, wrong, attempt_id),
        )
    return {"correct": correct, "wrong": wrong}


def finish_attempt(attempt_id: int) -> dict:
    counts = update_attempt_counts(attempt_id)
    with db_cursor() as cur:
        cur.execute(
            "UPDATE attempts SET status='finished', finished_at=datetime('now') WHERE id=?",
            (attempt_id,),
        )
    return counts


def list_user_attempts(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM attempts WHERE user_id=? ORDER BY started_at DESC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def user_stats(user_id: int) -> dict:
    conn = get_db()
    row = conn.execute(
        """SELECT COUNT(*) AS attempts_count,
                  COALESCE(SUM(correct_count),0) AS total_correct,
                  COALESCE(SUM(wrong_count),0) AS total_wrong
           FROM attempts WHERE user_id=? AND status='finished'""",
        (user_id,),
    ).fetchone()
    return dict(row)


# ---------- Kunlik seriya (streak) ----------

def _freeze_available(freeze_log: list, today: str) -> bool:
    """Oxirgi 7 kun ichida 'streak freeze' ishlatilmagan bo'lsa True."""
    cutoff = datetime.date.fromisoformat(today) - datetime.timedelta(days=7)
    return not any(datetime.date.fromisoformat(d) > cutoff for d in freeze_log if d)


def update_streak_on_finish(telegram_id: int) -> dict:
    """Test yakunlanganda chaqiriladi. Bir kunda bir nechta test tugatilsa
    ham seriya faqat bir marta oshadi (kun almashganda).
    "Streak freeze": har 7 kunlik oynada 1 marta, aynan 1 kun o'tkazib
    yuborilgan bo'lsa ham, seriya buzilmaydi (davom etadi)."""
    today = _today_str()
    user = get_user(telegram_id)
    last_date = user.get("last_test_date")
    current = user.get("current_streak") or 0
    longest = user.get("longest_streak") or 0
    try:
        freeze_log = json.loads(user.get("streak_freeze_log") or "[]")
    except (TypeError, ValueError):
        freeze_log = []
    freeze_used_now = False

    yesterday = (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat()
    day_before_yesterday = (datetime.date.fromisoformat(today) - datetime.timedelta(days=2)).isoformat()

    if last_date == today:
        pass  # bugun allaqachon hisoblangan
    elif last_date == yesterday:
        current += 1
    elif last_date == day_before_yesterday and _freeze_available(freeze_log, today):
        # Faqat 1 kun o'tkazib yuborilgan va muzlatish mavjud — seriya davom etadi
        current += 1
        freeze_log.append(today)
        freeze_used_now = True
    else:
        current = 1
    longest = max(longest, current)

    # 7 kundan eskirgan yozuvlarni tozalab boramiz
    cutoff = datetime.date.fromisoformat(today) - datetime.timedelta(days=7)
    freeze_log = [d for d in freeze_log if d and datetime.date.fromisoformat(d) > cutoff]

    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET current_streak=?, longest_streak=?, last_test_date=?, streak_freeze_log=? WHERE telegram_id=?",
            (current, longest, today, json.dumps(freeze_log), telegram_id),
        )
    return {
        "current": current, "longest": longest,
        "freeze_used": freeze_used_now,
        "freeze_available": _freeze_available(freeze_log, today),
    }


def streak_status(telegram_id: int) -> dict:
    """/api/stats uchun — test tugatmasdan ham joriy seriya va
    streak-freeze holatini qaytaradi."""
    user = get_user(telegram_id)
    today = _today_str()
    try:
        freeze_log = json.loads(user.get("streak_freeze_log") or "[]")
    except (TypeError, ValueError):
        freeze_log = []
    return {
        "current": user.get("current_streak") or 0,
        "longest": user.get("longest_streak") or 0,
        "freeze_available": _freeze_available(freeze_log, today),
    }


# ---------- Yutuqlar (achievements) ----------

def get_earned_achievements(telegram_id: int) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT achievement_key, earned_at FROM user_achievements WHERE user_id=?",
        (telegram_id,),
    ).fetchall()
    return {r["achievement_key"]: r["earned_at"] for r in rows}


def _award(telegram_id: int, key: str, earned: dict, newly: list) -> None:
    if key in earned:
        return
    with db_cursor() as cur:
        cur.execute(
            "INSERT OR IGNORE INTO user_achievements (user_id, achievement_key) VALUES (?,?)",
            (telegram_id, key),
        )
    newly.append(key)


def award_achievements(telegram_id: int, current_streak: int,
                        perfect_score: bool, attempts_count: int) -> list[str]:
    """Test yakunlangach shartlarni tekshirib, yangi yutuqlarni yozadi.
    Qaytadi: shu safar yangi qo'lga kiritilgan yutuqlar ro'yxati."""
    earned = get_earned_achievements(telegram_id)
    stats = user_stats(telegram_id)
    total_correct = stats["total_correct"]
    newly: list[str] = []

    if attempts_count >= 1:
        _award(telegram_id, "first_test", earned, newly)
    if current_streak >= 3:
        _award(telegram_id, "streak_3", earned, newly)
    if current_streak >= 7:
        _award(telegram_id, "streak_7", earned, newly)
    if current_streak >= 30:
        _award(telegram_id, "streak_30", earned, newly)
    if total_correct >= 50:
        _award(telegram_id, "correct_50", earned, newly)
    if total_correct >= 200:
        _award(telegram_id, "correct_200", earned, newly)
    if total_correct >= 1000:
        _award(telegram_id, "correct_1000", earned, newly)
    if perfect_score:
        _award(telegram_id, "perfect_score", earned, newly)
    return newly


def all_achievements_status(telegram_id: int) -> list[dict]:
    earned = get_earned_achievements(telegram_id)
    return [
        {"key": key, "earned": key in earned, "earned_at": earned.get(key)}
        for key in ACHIEVEMENTS
    ]


# ---------- Mavzular kesimidagi statistika ----------

def weak_operations(telegram_id: int, limit: int = 12) -> list[dict]:
    """Foydalanuvchi eng ko'p xato qilgan amallarni (mavzularni) aniqlaydi —
    'Xatolarni qayta ko'rish' rejimi uchun. Har biriga o'rtacha daraja
    (digits) va nechta marta xato qilinganini qaytaradi."""
    conn = get_db()
    rows = conn.execute(
        """SELECT q.operation AS operation,
                  COUNT(*) AS wrong_count,
                  AVG(CASE WHEN a.digits > 0 THEN a.digits END) AS avg_digits,
                  MAX(q.answered_at) AS last_wrong_at
           FROM questions q
           JOIN attempts a ON a.id = q.attempt_id
           WHERE a.user_id = ? AND q.is_correct = 0 AND q.status = 'answered'
           GROUP BY q.operation
           ORDER BY wrong_count DESC, last_wrong_at DESC
           LIMIT ?""",
        (telegram_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        avg_digits = r["avg_digits"]
        level = round(avg_digits) if avg_digits else 3
        level = max(1, min(5, level))
        out.append({"operation": r["operation"], "wrong_count": r["wrong_count"], "level": level})
    return out


def topic_stats(telegram_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT q.operation AS operation,
                  COUNT(*) AS total,
                  SUM(CASE WHEN q.is_correct=1 THEN 1 ELSE 0 END) AS correct
           FROM questions q
           JOIN attempts a ON a.id = q.attempt_id
           WHERE a.user_id = ? AND q.status IN ('answered', 'timeout')
           GROUP BY q.operation""",
        (telegram_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------- Moslashuvchan daraja tavsiyasi ----------

def last_attempt_for_operation(telegram_id: int, operation: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        """SELECT * FROM attempts
           WHERE user_id=? AND operation=? AND status='finished'
           ORDER BY finished_at DESC LIMIT 1""",
        (telegram_id, operation),
    ).fetchone()
    return dict(row) if row else None


# ---------- Reyting (leaderboard) ----------

def leaderboard(limit: int = 10) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT u.telegram_id, u.first_name, u.last_name,
                  COALESCE(SUM(a.correct_count), 0) AS points
           FROM users u
           JOIN attempts a ON a.user_id = u.telegram_id AND a.status='finished'
           GROUP BY u.telegram_id
           HAVING points > 0
           ORDER BY points DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def user_rank(telegram_id: int) -> Optional[dict]:
    stats = user_stats(telegram_id)
    points = stats["total_correct"]
    if points <= 0:
        return None
    conn = get_db()
    row = conn.execute(
        """SELECT COUNT(*) AS n FROM (
             SELECT a.user_id AS uid, SUM(a.correct_count) AS pts
             FROM attempts a WHERE a.status='finished'
             GROUP BY a.user_id
             HAVING pts > ?
           )""",
        (points,),
    ).fetchone()
    return {"rank": (row["n"] or 0) + 1, "points": points}


def inactive_users(days: int = 2) -> list[dict]:
    """`days` kundan beri test yechmagan (yoki umuman yechmagan, lekin
    kamida 1 kun oldin ro'yxatdan o'tgan) foydalanuvchilar — eslatma
    yuborish uchun (send_reminders.py)."""
    threshold = (datetime.datetime.utcnow().date() - datetime.timedelta(days=days)).isoformat()
    yesterday = (datetime.datetime.utcnow().date() - datetime.timedelta(days=1)).isoformat()
    conn = get_db()
    rows = conn.execute(
        """SELECT telegram_id, first_name, language FROM users
           WHERE date(registered_at) <= ?
             AND (last_test_date IS NULL OR last_test_date <= ?)""",
        (yesterday, threshold),
    ).fetchall()
    return [dict(r) for r in rows]


def admin_analytics(days: int = 7) -> dict:
    """Admin panel uchun oddiy analitika: kunlik faol foydalanuvchilar
    (DAU) soni (oxirgi `days` kun) va eng ko'p yechilgan mavzular
    (operatsiyalar bo'yicha savollar soni)."""
    conn = get_db()
    cutoff = (datetime.datetime.utcnow().date() - datetime.timedelta(days=days - 1)).isoformat()

    dau_rows = conn.execute(
        """SELECT substr(a.finished_at, 1, 10) AS day,
                  COUNT(DISTINCT a.user_id) AS active_users
           FROM attempts a
           WHERE a.status = 'finished' AND a.finished_at IS NOT NULL
                 AND substr(a.finished_at, 1, 10) >= ?
           GROUP BY day
           ORDER BY day""",
        (cutoff,),
    ).fetchall()
    dau_by_day = {r["day"]: r["active_users"] for r in dau_rows}
    daily_active = []
    for i in range(days):
        day = (datetime.datetime.utcnow().date() - datetime.timedelta(days=days - 1 - i)).isoformat()
        daily_active.append({"day": day, "active_users": dau_by_day.get(day, 0)})

    topic_rows = conn.execute(
        """SELECT q.operation AS operation, COUNT(*) AS total
           FROM questions q
           WHERE q.status IN ('answered', 'timeout')
           GROUP BY q.operation
           ORDER BY total DESC
           LIMIT 12"""
    ).fetchall()
    popular_topics = [{"operation": r["operation"], "total": r["total"]} for r in topic_rows]

    total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    total_attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts WHERE status='finished'").fetchone()["c"]
    total_questions_answered = conn.execute(
        "SELECT COUNT(*) AS c FROM questions WHERE status IN ('answered','timeout')"
    ).fetchone()["c"]

    return {
        "daily_active": daily_active,
        "popular_topics": popular_topics,
        "total_users": total_users,
        "total_attempts": total_attempts,
        "total_questions_answered": total_questions_answered,
    }


def all_users_with_stats() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT u.telegram_id, u.first_name, u.last_name, u.father_name,
                  u.username, u.is_admin, u.registered_at,
                  u.current_streak, u.longest_streak, u.language,
                  COUNT(a.id) AS attempts_count,
                  COALESCE(SUM(a.correct_count),0) AS total_correct,
                  COALESCE(SUM(a.wrong_count),0) AS total_wrong
           FROM users u
           LEFT JOIN attempts a ON a.user_id = u.telegram_id AND a.status='finished'
           GROUP BY u.telegram_id
           ORDER BY u.registered_at DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


# ---------- Guruh/sinf va uy vazifasi tizimi ----------

_JOIN_CODE_ALPHABET = string.ascii_uppercase + string.digits
_JOIN_CODE_AMBIGUOUS = set("O0I1")  # chalkashtiruvchi belgilarni chiqarib tashlaymiz
_JOIN_CODE_CHARS = [c for c in _JOIN_CODE_ALPHABET if c not in _JOIN_CODE_AMBIGUOUS]


def _generate_join_code(length: int = 6) -> str:
    return "".join(random.choices(_JOIN_CODE_CHARS, k=length))


def create_group(name: str, owner_id: int) -> dict:
    conn = get_db()
    for _ in range(10):
        code = _generate_join_code()
        exists = conn.execute("SELECT 1 FROM groups WHERE join_code=?", (code,)).fetchone()
        if not exists:
            break
    else:
        raise RuntimeError("Noyob qo'shilish kodi yaratib bo'lmadi")

    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO groups (name, join_code, owner_id) VALUES (?,?,?)",
            (name, code, owner_id),
        )
        group_id = cur.lastrowid
        cur.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?,?)",
            (group_id, owner_id),
        )
    return get_group(group_id)


def get_group(group_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
    return dict(row) if row else None


def get_group_by_join_code(join_code: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM groups WHERE join_code=?", (join_code.strip().upper(),)
    ).fetchone()
    return dict(row) if row else None


def join_group(join_code: str, user_id: int) -> Optional[dict]:
    group = get_group_by_join_code(join_code)
    if not group:
        return None
    with db_cursor() as cur:
        cur.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?,?)",
            (group["id"], user_id),
        )
    return group


def is_group_member(group_id: int, user_id: int) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM group_members WHERE group_id=? AND user_id=?", (group_id, user_id)
    ).fetchone()
    return row is not None


def user_groups(user_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT g.*, COUNT(gm2.id) AS member_count,
                  (g.owner_id = ?) AS is_owner
           FROM groups g
           JOIN group_members gm ON gm.group_id = g.id AND gm.user_id = ?
           LEFT JOIN group_members gm2 ON gm2.group_id = g.id
           GROUP BY g.id
           ORDER BY g.created_at DESC""",
        (user_id, user_id),
    ).fetchall()
    return [dict(r) for r in rows]


def group_members(group_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT u.telegram_id, u.first_name, u.last_name,
                  COALESCE(SUM(a.correct_count), 0) AS total_correct,
                  COUNT(a.id) AS attempts_count
           FROM group_members gm
           JOIN users u ON u.telegram_id = gm.user_id
           LEFT JOIN attempts a ON a.user_id = u.telegram_id AND a.status = 'finished'
           WHERE gm.group_id = ?
           GROUP BY u.telegram_id
           ORDER BY total_correct DESC""",
        (group_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def create_homework(group_id: int, operation: str, digits: int, question_count: int,
                     time_per_q: int, created_by: int, due_at: Optional[str] = None) -> int:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO homework
               (group_id, operation, digits, question_count, time_per_q, created_by, due_at)
               VALUES (?,?,?,?,?,?,?)""",
            (group_id, operation, digits, question_count, time_per_q, created_by, due_at),
        )
        return cur.lastrowid


def get_homework(homework_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM homework WHERE id=?", (homework_id,)).fetchone()
    return dict(row) if row else None


def list_homework(group_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM homework WHERE group_id=? ORDER BY created_at DESC", (group_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def homework_status_for_user(homework_id: int, user_id: int) -> Optional[dict]:
    """Berilgan foydalanuvchi shu uy vazifasini bajarganmi — bajargan
    bo'lsa natijasini qaytaradi (eng so'nggi urinish)."""
    conn = get_db()
    row = conn.execute(
        """SELECT * FROM attempts
           WHERE homework_id=? AND user_id=? AND status='finished'
           ORDER BY finished_at DESC LIMIT 1""",
        (homework_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def homework_completion(homework_id: int, group_id: int) -> list[dict]:
    """Guruh a'zolarining shu uy vazifasini bajarish holati (owner uchun)."""
    members = group_members(group_id)
    out = []
    for m in members:
        status = homework_status_for_user(homework_id, m["telegram_id"])
        out.append({
            "telegram_id": m["telegram_id"],
            "first_name": m["first_name"],
            "last_name": m["last_name"],
            "completed": status is not None,
            "correct_count": status["correct_count"] if status else None,
            "total_questions": status["total_questions"] if status else None,
        })
    return out


# ---------- Do'stni chaqirish (async duel) ----------
# Haqiqiy real-vaqtli (WebSocket) multiplayer o'rniga: yaratuvchi BIR MARTA
# qat'iy savollar to'plamini generatsiya qiladi, do'stiga kod/havola
# ulashadi, do'sti xohlagan vaqtda xuddi shu savollarga javob beradi va
# ikkalasi tugatgach natijalar taqqoslanadi (PythonAnywhere bepul
# webhook-asosidagi hostingda doimiy WebSocket ulanishi yo'qligi sababli).

_DUEL_CODE_CHARS = _JOIN_CODE_CHARS  # bir xil (chalkashtiruvchi belgilarsiz) alifbo


def _generate_duel_code(length: int = 6) -> str:
    return "".join(random.choices(_DUEL_CODE_CHARS, k=length))


def create_duel(creator_id: int, operation: str, digits: int, question_count: int,
                 time_per_q: int, questions: list) -> dict:
    """Duel yaratadi, savollar to'plamini QOTIB QOLDIRADI (bir marta
    generatsiya qilinadi) va yaratuvchining o'z urinishini ham darhol
    boshlaydi."""
    conn = get_db()
    for _ in range(10):
        code = _generate_duel_code()
        exists = conn.execute("SELECT 1 FROM duels WHERE join_code=?", (code,)).fetchone()
        if not exists:
            break
    else:
        raise RuntimeError("Noyob duel kodi yaratib bo'lmadi")

    questions_json = json.dumps(questions)
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO duels
               (creator_id, operation, digits, question_count, time_per_q, join_code, questions_json)
               VALUES (?,?,?,?,?,?,?)""",
            (creator_id, operation, digits, question_count, time_per_q, code, questions_json),
        )
        duel_id = cur.lastrowid

    creator_attempt_id = create_attempt(
        user_id=creator_id, operation=operation, digits=digits,
        time_per_q=time_per_q, total_questions=question_count, duel_id=duel_id,
    )
    add_questions(creator_attempt_id, questions)
    with db_cursor() as cur:
        cur.execute("UPDATE duels SET creator_attempt_id=? WHERE id=?", (creator_attempt_id, duel_id))

    duel = get_duel(duel_id)
    duel["creator_attempt_id"] = creator_attempt_id
    return duel


def get_duel(duel_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute("SELECT * FROM duels WHERE id=?", (duel_id,)).fetchone()
    return dict(row) if row else None


def get_duel_by_join_code(join_code: str) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM duels WHERE join_code=?", (join_code.strip().upper(),)
    ).fetchone()
    return dict(row) if row else None


def join_duel(join_code: str, opponent_id: int) -> Optional[dict]:
    """Do'st kodni kiritib duelga qo'shiladi — AGAR u allaqachon
    (o'zi yaratuvchi bo'lmasa va) hali boshqa raqib qo'shilmagan bo'lsa.
    Muvaffaqiyatli bo'lsa duel + opponent_attempt_id qaytaradi; aks holda
    None (kod noto'g'ri) yoki "already_taken"/"own_duel" xato belgisini
    ko'targan holda chaqiruvchi tomonidan tekshiriladi."""
    duel = get_duel_by_join_code(join_code)
    if not duel:
        return None
    if duel["creator_id"] == opponent_id:
        return {"error": "own_duel"}
    if duel["opponent_id"] and duel["opponent_id"] != opponent_id:
        return {"error": "already_taken"}
    if duel["opponent_id"] == opponent_id and duel["opponent_attempt_id"]:
        # Allaqachon qo'shilgan — mavjud urinishini qaytaramiz (qayta boshlamaydi)
        duel["opponent_attempt_id_existing"] = True
        return duel

    questions = json.loads(duel["questions_json"])
    opponent_attempt_id = create_attempt(
        user_id=opponent_id, operation=duel["operation"], digits=duel["digits"],
        time_per_q=duel["time_per_q"], total_questions=duel["question_count"], duel_id=duel["id"],
    )
    add_questions(opponent_attempt_id, questions)
    with db_cursor() as cur:
        cur.execute(
            "UPDATE duels SET opponent_id=?, opponent_attempt_id=? WHERE id=?",
            (opponent_id, opponent_attempt_id, duel["id"]),
        )
    duel = get_duel(duel["id"])
    duel["opponent_attempt_id"] = opponent_attempt_id
    return duel


def duel_result(duel_id: int, viewer_id: int) -> Optional[dict]:
    """Ikkala tomonning natijasini (agar tugatilgan bo'lsa) qaytaradi."""
    duel = get_duel(duel_id)
    if not duel:
        return None
    if viewer_id not in (duel["creator_id"], duel["opponent_id"]):
        return None

    def _side(user_id, attempt_id):
        if not user_id or not attempt_id:
            return None
        user = get_user(user_id)
        attempt = get_attempt(attempt_id)
        finished = bool(attempt and attempt["status"] == "finished")
        return {
            "telegram_id": user_id,
            "first_name": user["first_name"] if user else "",
            "last_name": user["last_name"] if user else "",
            "finished": finished,
            "correct_count": attempt["correct_count"] if finished else None,
            "total_questions": attempt["total_questions"] if attempt else duel["question_count"],
        }

    creator_side = _side(duel["creator_id"], duel["creator_attempt_id"])
    opponent_side = _side(duel["opponent_id"], duel["opponent_attempt_id"])
    both_finished = bool(creator_side and creator_side["finished"] and opponent_side and opponent_side["finished"])
    return {
        "duel_id": duel_id,
        "operation": duel["operation"],
        "digits": duel["digits"],
        "join_code": duel["join_code"],
        "creator": creator_side,
        "opponent": opponent_side,
        "both_finished": both_finished,
    }
