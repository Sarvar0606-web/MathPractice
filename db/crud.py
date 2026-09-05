"""Ma'lumotlar bazasi bilan ishlash funksiyalari (CRUD)."""
import json
from typing import Optional

from config import ADMIN_IDS
from db.database import db_cursor, get_db


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
            cur.execute(
                """INSERT INTO users
                   (telegram_id, first_name, last_name, father_name,
                    birth_year, birth_month, birth_day, username, is_admin, language)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (telegram_id, first_name, last_name, father_name, birth_year,
                 birth_month, birth_day, username, is_admin, language or "uz"),
            )
    return get_user(telegram_id)


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
            cur.execute(
                """INSERT INTO questions
                   (attempt_id, order_index, operand_a, operand_b, operand_c,
                    operand_d, operation, correct_answer, choices, display_text)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (attempt_id, idx, q["a"], q["b"], q.get("c"), q.get("d"),
                 q["operation"], q["answer"], json.dumps(q["choices"]),
                 q.get("display_text")),
            )


def get_attempt(attempt_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
    ).fetchone()
    return dict(row) if row else None


def get_attempt_questions(attempt_id: int) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM questions WHERE attempt_id = ? ORDER BY order_index",
        (attempt_id,),
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["choices"] = json.loads(d["choices"])
        result.append(d)
    return result


def get_question(question_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM questions WHERE id = ?", (question_id,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["choices"] = json.loads(d["choices"])
    return d


def get_next_pending_question(attempt_id: int) -> Optional[dict]:
    conn = get_db()
    row = conn.execute(
        """SELECT * FROM questions WHERE attempt_id = ? AND status = 'pending'
           ORDER BY order_index LIMIT 1""",
        (attempt_id,),
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["choices"] = json.loads(d["choices"])
    return d


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


def all_users_with_stats() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        """SELECT u.telegram_id, u.first_name, u.last_name, u.father_name,
                  u.username, u.is_admin, u.registered_at,
                  COUNT(a.id) AS attempts_count,
                  COALESCE(SUM(a.correct_count),0) AS total_correct,
                  COALESCE(SUM(a.wrong_count),0) AS total_wrong
           FROM users u
           LEFT JOIN attempts a ON a.user_id = u.telegram_id AND a.status='finished'
           GROUP BY u.telegram_id
           ORDER BY u.registered_at DESC"""
    ).fetchall()
    return [dict(r) for r in rows]
