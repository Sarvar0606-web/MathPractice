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
    operand_a       INTEGER NOT NULL,
    operand_b       INTEGER NOT NULL,
    operation       TEXT NOT NULL,
    correct_answer  INTEGER NOT NULL,
    choices         TEXT NOT NULL,
    selected_answer INTEGER,
    is_correct      INTEGER,
    status          TEXT NOT NULL DEFAULT 'pending',
    time_taken_ms   INTEGER,
    answered_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_questions_attempt ON questions(attempt_id);
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


def init_db():
    """Ilova ishga tushganda (request tashqarisida) sxema yaratiladi."""
    conn = _new_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
