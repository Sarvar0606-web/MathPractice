"""Ma'lumotlar bazasi bilan ishlash funksiyalari (CRUD)."""
import datetime
import json
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
                    time_per_q: int, total_questions: int) -> int:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO attempts
               (user_id, operation, digits, time_per_q, total_questions)
               VALUES (?,?,?,?,?)""",
            (user_id, operation, digits, time_per_q, total_questions),
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

def update_streak_on_finish(telegram_id: int) -> dict:
    """Test yakunlanganda chaqiriladi. Bir kunda bir nechta test tugatilsa
    ham seriya faqat bir marta oshadi (kun almashganda)."""
    today = _today_str()
    user = get_user(telegram_id)
    last_date = user.get("last_test_date")
    current = user.get("current_streak") or 0
    longest = user.get("longest_streak") or 0

    if last_date == today:
        pass  # bugun allaqachon hisoblangan
    elif last_date == (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat():
        current += 1
    else:
        current = 1
    longest = max(longest, current)

    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET current_streak=?, longest_streak=?, last_test_date=? WHERE telegram_id=?",
            (current, longest, today, telegram_id),
        )
    return {"current": current, "longest": longest}


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
