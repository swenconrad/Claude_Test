"""SQLite database initialization and connection management."""

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".jobapp" / "jobs.db"


def get_db_path() -> Path:
    """Return the database file path, respecting JOBAPP_DB_PATH env var."""
    env_path = os.environ.get("JOBAPP_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a connection to the SQLite database, creating it if needed."""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't exist."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            linkedin TEXT NOT NULL DEFAULT '',
            github TEXT NOT NULL DEFAULT '',
            website TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            skills TEXT NOT NULL DEFAULT '',
            experience TEXT NOT NULL DEFAULT '',
            education TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            salary TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'saved'
                CHECK (status IN (
                    'saved', 'applied', 'phone_screen',
                    'interview', 'offer', 'rejected', 'withdrawn'
                )),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            applied_at TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS cover_letter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL REFERENCES job(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()
