"""SQLite ulanishi va sxema (schema) yaratish (Flask 'g' orqali)."""
import sqlite3
from contextlib import contextmanager

from flask import g

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id     INTEGER PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    father_name     TEXT NOT NULL,
    birth_year      INTEGER NOT NULL,
    birth_month     INTEGER NOT NULL,
    birth_day       INTEGER NOT NULL,
    username        TEXT,
    is_admin        INTEGER NOT NULL DEFAULT 0,
    language        TEXT NOT NULL DEFAULT 'uz',
    registered_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(telegram_id),
    operation       TEXT NOT NULL,
    digits          INTEGER NOT NULL,
    time_per_q      INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    correct_count   INTEGER NOT NULL DEFAULT 0,
    wrong_count     INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'in_progress',
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at     TEXT
);

CREATE TABLE IF NOT EXISTS questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id      INTEGER NOT NULL REFERENCES attempts(id),
    order_index     INTEGER NOT NULL,
    operand_a       INTEGER,
    operand_b       INTEGER,
    operand_c       INTEGER,
    operand_d       INTEGER,
    operation       TEXT NOT NULL,
    correct_answer  TEXT NOT NULL,
    choices         TEXT NOT NULL,
    selected_answer TEXT,
    is_correct      INTEGER,
    status          TEXT NOT NULL DEFAULT 'pending',
    time_taken_ms   INTEGER,
    answered_at     TEXT,
    display_text    TEXT,
    extra_data      TEXT
);

CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_questions_attempt ON questions(attempt_id);

CREATE TABLE IF NOT EXISTS user_achievements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(telegram_id),
    achievement_key TEXT NOT NULL,
    earned_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, achievement_key)
);

CREATE TABLE IF NOT EXISTS pending_referrals (
    telegram_id     INTEGER PRIMARY KEY,
    referrer_code   TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _new_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    """Joriy so'rov (request) davomida bitta ulanishni qayta ishlatadi."""
    if "db" not in g:
        g.db = _new_conn()
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def db_cursor():
    conn = get_db()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _migrate_legacy_questions_table(conn: sqlite3.Connection) -> None:
    """Eski (operand_c/d'siz, INTEGER javobli) 'questions' jadvalini yangi
    sxemaga (kasrlar uchun operand_c/d, matnli javoblar) ko'chiradi.
    Mavjud ma'lumotlar yo'qolmaydi. Agar jadval allaqachon yangi bo'lsa,
    hech narsa qilmaydi (idempotent)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(questions)")}
    if not cols or "operand_c" in cols:
        return  # jadval mavjud emas (yangi DB) yoki allaqachon migratsiya qilingan

    conn.execute("DROP INDEX IF EXISTS idx_questions_attempt")
    conn.execute("ALTER TABLE questions RENAME TO questions_old")
    conn.executescript(SCHEMA)  # 'questions' jadvalini yangi ko'rinishda qayta yaratadi
    conn.execute(
        """INSERT INTO questions
           (id, attempt_id, order_index, operand_a, operand_b, operand_c, operand_d,
            operation, correct_answer, choices, selected_answer, is_correct,
            status, time_taken_ms, answered_at)
           SELECT id, attempt_id, order_index, operand_a, operand_b, NULL, NULL,
                  operation, CAST(correct_answer AS TEXT), choices,
                  CASE WHEN selected_answer IS NULL THEN NULL ELSE CAST(selected_answer AS TEXT) END,
                  is_correct, status, time_taken_ms, answered_at
           FROM questions_old"""
    )
    conn.execute("DROP TABLE questions_old")
    conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, coltype: str) -> None:
    """Agar `table` jadvalida `column` ustuni bo'lmasa, uni qo'shadi
    (idempotent — allaqachon mavjud bo'lsa hech narsa qilmaydi)."""
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if not cols or column in cols:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
    conn.commit()


def init_db():
    """Ilova ishga tushganda (request tashqarisida) sxema yaratiladi."""
    conn = _new_conn()
    conn.executescript(SCHEMA)
    _migrate_legacy_questions_table(conn)
    _ensure_column(conn, "questions", "display_text", "TEXT")
    _ensure_column(conn, "questions", "extra_data", "TEXT")
    _ensure_column(conn, "users", "language", "TEXT NOT NULL DEFAULT 'uz'")
    _ensure_column(conn, "users", "current_streak", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(conn, "users", "longest_streak", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(conn, "users", "last_test_date", "TEXT")
    _ensure_column(conn, "users", "referral_code", "TEXT")
    _ensure_column(conn, "users", "referred_by_id", "INTEGER")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_referral_code "
        "ON users(referral_code) WHERE referral_code IS NOT NULL"
    )
    # Eski (referral tizimidan oldingi) foydalanuvchilarga ham kod beriladi.
    conn.execute(
        "UPDATE users SET referral_code = printf('%X', telegram_id) "
        "WHERE referral_code IS NULL"
    )
    conn.commit()
    conn.close()
