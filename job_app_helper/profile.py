"""Profile/resume management."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Profile:
    full_name: str
    email: str
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    website: str = ""
    summary: str = ""
    skills: str = ""
    experience: str = ""
    education: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Profile:
        return cls(
            full_name=row["full_name"],
            email=row["email"],
            phone=row["phone"],
            location=row["location"],
            linkedin=row["linkedin"],
            github=row["github"],
            website=row["website"],
            summary=row["summary"],
            skills=row["skills"],
            experience=row["experience"],
            education=row["education"],
        )


def save_profile(conn: sqlite3.Connection, profile: Profile) -> None:
    """Insert or replace the single profile row."""
    conn.execute(
        """
        INSERT OR REPLACE INTO profile
            (id, full_name, email, phone, location, linkedin, github,
             website, summary, skills, experience, education)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile.full_name,
            profile.email,
            profile.phone,
            profile.location,
            profile.linkedin,
            profile.github,
            profile.website,
            profile.summary,
            profile.skills,
            profile.experience,
            profile.education,
        ),
    )
    conn.commit()


def get_profile(conn: sqlite3.Connection) -> Profile | None:
    """Return the saved profile, or None if not set."""
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    if row is None:
        return None
    return Profile.from_row(row)


def update_profile_field(conn: sqlite3.Connection, field: str, value: str) -> bool:
    """Update a single profile field. Returns False if no profile exists."""
    valid_fields = {
        "full_name", "email", "phone", "location", "linkedin",
        "github", "website", "summary", "skills", "experience", "education",
    }
    if field not in valid_fields:
        raise ValueError(f"Invalid field: {field}. Valid fields: {', '.join(sorted(valid_fields))}")
    cur = conn.execute(f"UPDATE profile SET {field} = ? WHERE id = 1", (value,))
    conn.commit()
    return cur.rowcount > 0
