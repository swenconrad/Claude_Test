"""Cover letter generation from templates."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from string import Template

from job_app_helper.jobs import Job
from job_app_helper.profile import Profile

DEFAULT_TEMPLATE = """\
Dear Hiring Manager,

I am writing to express my interest in the $title position at $company. \
With my background and skills, I am confident I would be a strong addition to your team.

$summary

My key skills include: $skills

$experience_paragraph

I am excited about the opportunity to contribute to $company and would welcome \
the chance to discuss how my experience aligns with your needs.

Thank you for your time and consideration.

Sincerely,
$full_name
$email
$phone\
"""

CONCISE_TEMPLATE = """\
Dear Hiring Manager,

I am interested in the $title role at $company. $summary

Key skills: $skills

I look forward to discussing this opportunity.

$full_name | $email | $phone\
"""


TEMPLATES = {
    "default": DEFAULT_TEMPLATE,
    "concise": CONCISE_TEMPLATE,
}


@dataclass
class CoverLetter:
    id: int
    job_id: int
    content: str
    created_at: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> CoverLetter:
        return cls(
            id=row["id"],
            job_id=row["job_id"],
            content=row["content"],
            created_at=row["created_at"],
        )


def generate_cover_letter(
    profile: Profile,
    job: Job,
    template_name: str = "default",
) -> str:
    """Generate a cover letter by filling in a template with profile and job data."""
    if template_name not in TEMPLATES:
        raise ValueError(
            f"Unknown template: {template_name}. Available: {', '.join(TEMPLATES)}"
        )
    tmpl = Template(TEMPLATES[template_name])

    experience_lines = profile.experience.strip().splitlines()
    if experience_lines:
        experience_paragraph = (
            "In my most recent role, " + experience_lines[0].strip().lstrip("- ") + "."
        )
    else:
        experience_paragraph = ""

    return tmpl.safe_substitute(
        title=job.title,
        company=job.company,
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        summary=profile.summary,
        skills=profile.skills,
        experience_paragraph=experience_paragraph,
    )


def save_cover_letter(conn: sqlite3.Connection, job_id: int, content: str) -> int:
    """Save a generated cover letter and return its ID."""
    cur = conn.execute(
        "INSERT INTO cover_letter (job_id, content) VALUES (?, ?)",
        (job_id, content),
    )
    conn.commit()
    return cur.lastrowid


def get_cover_letters(conn: sqlite3.Connection, job_id: int) -> list[CoverLetter]:
    """Return all cover letters for a given job."""
    rows = conn.execute(
        "SELECT * FROM cover_letter WHERE job_id = ? ORDER BY created_at DESC",
        (job_id,),
    ).fetchall()
    return [CoverLetter.from_row(r) for r in rows]
