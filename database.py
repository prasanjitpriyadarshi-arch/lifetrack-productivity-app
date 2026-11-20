"""SQLite storage and small, beginner-friendly data helpers for LifeTrack."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sqlite3
from typing import Any, Iterator

import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "lifetrack.db"

TABLE_COLUMNS: dict[str, set[str]] = {
    "activities": {"title", "category", "start_time", "end_time", "notes", "active"},
    "activity_logs": {"activity_id", "log_date", "completed"},
    "workouts": {"workout_date", "exercise", "duration_minutes", "notes"},
    "meditation": {"meditation_date", "duration_minutes", "completed", "notes"},
    "study_sessions": {"session_date", "study_type", "subject", "topic", "duration_minutes", "notes"},
    "skill_sessions": {"skill_name", "topic", "time_spent_minutes", "learning_date", "progress_status", "notes"},
    "sleep_records": {"record_date", "bedtime", "wake_time", "duration_minutes", "notes"},
    "screen_time": {"record_date", "app_name", "minutes", "productive"},
    "habits": {"name", "active"},
    "habit_logs": {"habit_id", "log_date", "completed"},
    "goals": {"title", "description", "goal_period", "deadline", "priority", "status"},
    "journal": {"entry_date", "achievements", "learned", "challenges", "mood", "tomorrow_priorities"},
}

ORDER_COLUMNS: dict[str, set[str]] = {
    "activities": {"start_time", "title", "id"},
    "activity_logs": {"log_date", "id"},
    "workouts": {"workout_date", "id"},
    "meditation": {"meditation_date", "id"},
    "study_sessions": {"session_date", "id"},
    "skill_sessions": {"learning_date", "id"},
    "sleep_records": {"record_date", "id"},
    "screen_time": {"record_date", "app_name", "id"},
    "habits": {"name", "id"},
    "habit_logs": {"log_date", "id"},
    "goals": {"deadline", "created_at", "id"},
    "journal": {"entry_date", "id"},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    log_date TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(activity_id, log_date)
);
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_date TEXT NOT NULL,
    exercise TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS meditation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meditation_date TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    completed INTEGER NOT NULL DEFAULT 1,
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_date TEXT NOT NULL,
    study_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    topic TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS skill_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    topic TEXT NOT NULL,
    time_spent_minutes INTEGER NOT NULL CHECK(time_spent_minutes > 0),
    learning_date TEXT NOT NULL,
    progress_status TEXT NOT NULL DEFAULT 'In progress',
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS sleep_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date TEXT NOT NULL UNIQUE,
    bedtime TEXT NOT NULL,
    wake_time TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0 AND duration_minutes <= 1440),
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS screen_time (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date TEXT NOT NULL,
    app_name TEXT NOT NULL,
    minutes INTEGER NOT NULL CHECK(minutes >= 0),
    productive INTEGER NOT NULL DEFAULT 0,
    UNIQUE(record_date, app_name)
);
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS habit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    log_date TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    UNIQUE(habit_id, log_date)
);
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    goal_period TEXT NOT NULL,
    deadline TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'Medium',
    status TEXT NOT NULL DEFAULT 'In progress',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL UNIQUE,
    achievements TEXT NOT NULL DEFAULT '',
    learned TEXT NOT NULL DEFAULT '',
    challenges TEXT NOT NULL DEFAULT '',
    mood TEXT NOT NULL DEFAULT 'Okay',
    tomorrow_priorities TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(workout_date);
CREATE INDEX IF NOT EXISTS idx_study_date ON study_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_screen_date ON screen_time(record_date);
CREATE INDEX IF NOT EXISTS idx_habit_logs_date ON habit_logs(log_date);
"""

DEFAULT_ROUTINE = [
    ("Wake up", "Personal", "06:00", "06:15"),
    ("Meditation", "Meditation", "06:15", "06:30"),
    ("Exercise / Gym", "Gym", "06:30", "07:30"),
    ("Breakfast and preparation", "Personal", "07:30", "09:00"),
    ("College", "College", "09:00", "16:00"),
    ("Rest", "Personal", "16:30", "17:00"),
    ("College study", "Study", "17:00", "18:30"),
    ("Python / DSA / AI-ML", "Skills", "18:30", "19:30"),
    ("Dinner", "Personal", "19:30", "20:00"),
    ("Extra study and revision", "Study", "20:00", "21:00"),
    ("Reading and journal", "Personal", "21:00", "22:00"),
    ("Sleep", "Sleep", "22:00", "06:00"),
]

DEFAULT_HABITS = [
    "Wake up on time",
    "Meditation",
    "Gym",
    "College study",
    "Extra study",
    "Skill learning",
    "Reading",
    "Sleep on time",
]


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Open a connection and commit only when all work succeeds."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    """Create tables and add sample routine/habits once, without overwriting data."""
    with connection() as conn:
        conn.executescript(SCHEMA)
        routine_seeded = conn.execute(
            "SELECT value FROM app_settings WHERE key = 'routine_seeded'"
        ).fetchone()
        if not routine_seeded:
            conn.executemany(
                "INSERT INTO activities (title, category, start_time, end_time) VALUES (?, ?, ?, ?)",
                DEFAULT_ROUTINE,
            )
            conn.execute("INSERT INTO app_settings (key, value) VALUES ('routine_seeded', '1')")

        habits_seeded = conn.execute(
            "SELECT value FROM app_settings WHERE key = 'habits_seeded'"
        ).fetchone()
        if not habits_seeded:
            conn.executemany(
                "INSERT OR IGNORE INTO habits (name) VALUES (?)",
                [(name,) for name in DEFAULT_HABITS],
            )
            conn.execute("INSERT INTO app_settings (key, value) VALUES ('habits_seeded', '1')")


def read_table(table: str, order_by: str = "id DESC", active_only: bool = False) -> pd.DataFrame:
    """Return a table as a Pandas DataFrame; table/order names are allow-listed."""
    if table not in TABLE_COLUMNS:
        raise ValueError(f"Unknown table: {table}")
    column, _, direction = order_by.partition(" ")
    if column not in ORDER_COLUMNS[table] or (direction and direction.upper() not in {"ASC", "DESC"}):
        raise ValueError("Unsupported sort order")
    query = f"SELECT * FROM {table}"
    if active_only:
        if table not in {"activities", "habits"}:
            raise ValueError("Active filtering is only available for routines and habits")
        query += " WHERE active = 1"
    query += f" ORDER BY {column} {direction.upper() if direction else 'ASC'}"
    with connection() as conn:
        return pd.read_sql_query(query, conn)


def insert_record(table: str, values: dict[str, Any]) -> int:
    """Insert a validated row and return its new ID."""
    _validate_values(table, values)
    columns = list(values)
    placeholders = ", ".join("?" for _ in columns)
    query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    with connection() as conn:
        cursor = conn.execute(query, [values[column] for column in columns])
        return int(cursor.lastrowid)


def update_record(table: str, record_id: int, values: dict[str, Any]) -> None:
    """Update a validated row by its integer primary key."""
    _validate_values(table, values)
    assignments = ", ".join(f"{column} = ?" for column in values)
    with connection() as conn:
        conn.execute(
            f"UPDATE {table} SET {assignments} WHERE id = ?",
            [*values.values(), int(record_id)],
        )


def delete_record(table: str, record_id: int) -> None:
    """Delete a row by ID; related daily logs cascade from their parent."""
    if table not in TABLE_COLUMNS:
        raise ValueError(f"Unknown table: {table}")
    with connection() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id = ?", (int(record_id),))


def _validate_values(table: str, values: dict[str, Any]) -> None:
    if table not in TABLE_COLUMNS:
        raise ValueError(f"Unknown table: {table}")
    if not values or not set(values).issubset(TABLE_COLUMNS[table]):
        raise ValueError(f"Unsupported fields for {table}")


def upsert_daily_log(table: str, id_column: str, item_id: int, log_date: date, completed: bool) -> None:
    """Save a daily completion flag for a routine activity or habit."""
    allowed = {("activity_logs", "activity_id"), ("habit_logs", "habit_id")}
    if (table, id_column) not in allowed:
        raise ValueError("Unsupported daily log")
    with connection() as conn:
        conn.execute(
            f"INSERT INTO {table} ({id_column}, log_date, completed) VALUES (?, ?, ?) "
            f"ON CONFLICT({id_column}, log_date) DO UPDATE SET completed = excluded.completed",
            (int(item_id), log_date.isoformat(), int(completed)),
        )


def upsert_screen_time(record_date: date, app_name: str, minutes: int, productive: bool) -> None:
    """Store one total per app and date, replacing it on subsequent edits."""
    if minutes < 0:
        raise ValueError("Screen-time minutes cannot be negative")
    with connection() as conn:
        conn.execute(
            "INSERT INTO screen_time (record_date, app_name, minutes, productive) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(record_date, app_name) DO UPDATE SET minutes = excluded.minutes, "
            "productive = excluded.productive",
            (record_date.isoformat(), app_name.strip(), int(minutes), int(productive)),
        )


def get_setting(key: str, default: str = "") -> str:
    with connection() as conn:
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return str(row["value"]) if row else default


def set_setting(key: str, value: str) -> None:
    with connection() as conn:
        conn.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def calculate_sleep_minutes(bedtime: str | time, wake_time: str | time) -> int:
    """Calculate elapsed sleep, rolling the wake time into the next day if needed."""
    bed = time.fromisoformat(bedtime) if isinstance(bedtime, str) else bedtime
    wake = time.fromisoformat(wake_time) if isinstance(wake_time, str) else wake_time
    start = datetime.combine(date.today(), bed)
    end = datetime.combine(date.today(), wake)
    if end <= start:
        end += timedelta(days=1)
    minutes = int((end - start).total_seconds() // 60)
    if not 0 < minutes <= 1440:
        raise ValueError("Sleep duration must be between 1 minute and 24 hours")
    return minutes
