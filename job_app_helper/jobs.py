"""Job tracking and application management."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

VALID_STATUSES = (
    "saved", "applied", "phone_screen",
    "interview", "offer", "rejected", "withdrawn",
)

STATUS_DISPLAY = {
    "saved": "Saved",
    "applied": "Applied",
    "phone_screen": "Phone Screen",
    "interview": "Interview",
    "offer": "Offer",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
}


@dataclass
class Job:
    id: int
    company: str
    title: str
    url: str
    location: str
    salary: str
    description: str
    notes: str
    status: str
    created_at: str
    applied_at: str | None
    updated_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Job:
        return cls(
            id=row["id"],
            company=row["company"],
            title=row["title"],
            url=row["url"],
            location=row["location"],
            salary=row["salary"],
            description=row["description"],
            notes=row["notes"],
            status=row["status"],
            created_at=row["created_at"],
            applied_at=row["applied_at"],
            updated_at=row["updated_at"],
        )


def add_job(
    conn: sqlite3.Connection,
    company: str,
    title: str,
    url: str = "",
    location: str = "",
    salary: str = "",
    description: str = "",
    notes: str = "",
) -> int:
    """Add a new job and return its ID."""
    cur = conn.execute(
        """
        INSERT INTO job (company, title, url, location, salary, description, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (company, title, url, location, salary, description, notes),
    )
    conn.commit()
    return cur.lastrowid


def get_job(conn: sqlite3.Connection, job_id: int) -> Job | None:
    """Fetch a single job by ID."""
    row = conn.execute("SELECT * FROM job WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    return Job.from_row(row)


def list_jobs(
    conn: sqlite3.Connection,
    status: str | None = None,
) -> list[Job]:
    """List jobs, optionally filtered by status."""
    if status:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {', '.join(VALID_STATUSES)}")
        rows = conn.execute(
            "SELECT * FROM job WHERE status = ? ORDER BY updated_at DESC",
            (status,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM job ORDER BY updated_at DESC"
        ).fetchall()
    return [Job.from_row(r) for r in rows]


def update_job_status(conn: sqlite3.Connection, job_id: int, status: str) -> bool:
    """Update a job's status. Returns False if the job doesn't exist."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}. Valid: {', '.join(VALID_STATUSES)}")
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    applied_at_clause = ""
    params: list = [status, now]
    if status == "applied":
        applied_at_clause = ", applied_at = ?"
        params.append(now)
    params.append(job_id)
    cur = conn.execute(
        f"UPDATE job SET status = ?, updated_at = ?{applied_at_clause} WHERE id = ?",
        params,
    )
    conn.commit()
    return cur.rowcount > 0


def update_job_field(conn: sqlite3.Connection, job_id: int, field: str, value: str) -> bool:
    """Update a single field on a job. Returns False if the job doesn't exist."""
    valid_fields = {"company", "title", "url", "location", "salary", "description", "notes"}
    if field not in valid_fields:
        raise ValueError(f"Invalid field: {field}. Valid: {', '.join(sorted(valid_fields))}")
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    cur = conn.execute(
        f"UPDATE job SET {field} = ?, updated_at = ? WHERE id = ?",
        (value, now, job_id),
    )
    conn.commit()
    return cur.rowcount > 0


def delete_job(conn: sqlite3.Connection, job_id: int) -> bool:
    """Delete a job and its cover letters. Returns False if the job doesn't exist."""
    cur = conn.execute("DELETE FROM job WHERE id = ?", (job_id,))
    conn.commit()
    return cur.rowcount > 0


def get_stats(conn: sqlite3.Connection) -> dict[str, int]:
    """Return a count of jobs grouped by status."""
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM job GROUP BY status ORDER BY status"
    ).fetchall()
    return {row["status"]: row["cnt"] for row in rows}
