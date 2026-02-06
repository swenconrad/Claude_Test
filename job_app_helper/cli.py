"""Command-line interface for Job Application Helper."""

from __future__ import annotations

import argparse
import sys
import textwrap

from job_app_helper.cover_letter import (
    TEMPLATES,
    generate_cover_letter,
    get_cover_letters,
    save_cover_letter,
)
from job_app_helper.database import get_connection, init_db
from job_app_helper.jobs import (
    STATUS_DISPLAY,
    VALID_STATUSES,
    add_job,
    delete_job,
    get_job,
    get_stats,
    list_jobs,
    update_job_field,
    update_job_status,
)
from job_app_helper.profile import Profile, get_profile, save_profile, update_profile_field


# ── Helpers ──────────────────────────────────────────────────────────────────

def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a simple text table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in widths]))
    for row in rows:
        print(fmt.format(*row))


def _prompt(label: str, default: str = "") -> str:
    """Prompt the user for input with an optional default."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else default


# ── Profile commands ─────────────────────────────────────────────────────────

def cmd_profile_setup(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    existing = get_profile(conn)

    print("=== Profile Setup ===")
    print("Fill in your details (press Enter to keep existing value).\n")

    d = {
        "full_name": existing.full_name if existing else "",
        "email": existing.email if existing else "",
        "phone": existing.phone if existing else "",
        "location": existing.location if existing else "",
        "linkedin": existing.linkedin if existing else "",
        "github": existing.github if existing else "",
        "website": existing.website if existing else "",
        "summary": existing.summary if existing else "",
        "skills": existing.skills if existing else "",
        "experience": existing.experience if existing else "",
        "education": existing.education if existing else "",
    }

    d["full_name"] = _prompt("Full name", d["full_name"])
    d["email"] = _prompt("Email", d["email"])
    d["phone"] = _prompt("Phone", d["phone"])
    d["location"] = _prompt("Location", d["location"])
    d["linkedin"] = _prompt("LinkedIn URL", d["linkedin"])
    d["github"] = _prompt("GitHub URL", d["github"])
    d["website"] = _prompt("Website", d["website"])
    d["summary"] = _prompt("Professional summary", d["summary"])
    d["skills"] = _prompt("Skills (comma-separated)", d["skills"])
    d["experience"] = _prompt("Experience summary", d["experience"])
    d["education"] = _prompt("Education", d["education"])

    if not d["full_name"] or not d["email"]:
        print("Error: Full name and email are required.")
        sys.exit(1)

    save_profile(conn, Profile(**d))
    print("\nProfile saved.")


def cmd_profile_show(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    profile = get_profile(conn)
    if profile is None:
        print("No profile set up yet. Run: jobapp profile setup")
        return

    print("=== Your Profile ===")
    print(f"  Name:       {profile.full_name}")
    print(f"  Email:      {profile.email}")
    print(f"  Phone:      {profile.phone}")
    print(f"  Location:   {profile.location}")
    print(f"  LinkedIn:   {profile.linkedin}")
    print(f"  GitHub:     {profile.github}")
    print(f"  Website:    {profile.website}")
    print(f"  Summary:    {profile.summary}")
    print(f"  Skills:     {profile.skills}")
    print(f"  Experience: {profile.experience}")
    print(f"  Education:  {profile.education}")


def cmd_profile_update(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    if not update_profile_field(conn, args.field, args.value):
        print("No profile found. Run: jobapp profile setup")
        sys.exit(1)
    print(f"Updated '{args.field}'.")


# ── Job commands ─────────────────────────────────────────────────────────────

def cmd_job_add(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    job_id = add_job(
        conn,
        company=args.company,
        title=args.title,
        url=args.url or "",
        location=args.location or "",
        salary=args.salary or "",
        description=args.description or "",
        notes=args.notes or "",
    )
    print(f"Job #{job_id} added: {args.title} at {args.company}")


def cmd_job_list(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    jobs = list_jobs(conn, status=args.status)
    if not jobs:
        msg = f"No jobs with status '{args.status}'." if args.status else "No jobs tracked yet."
        print(msg)
        return

    rows = []
    for j in jobs:
        rows.append([
            str(j.id),
            j.company[:20],
            j.title[:25],
            STATUS_DISPLAY.get(j.status, j.status),
            j.applied_at or "-",
            j.location[:15] if j.location else "-",
        ])
    _print_table(["ID", "Company", "Title", "Status", "Applied", "Location"], rows)


def cmd_job_show(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    job = get_job(conn, args.id)
    if job is None:
        print(f"Job #{args.id} not found.")
        sys.exit(1)

    print(f"=== Job #{job.id} ===")
    print(f"  Company:     {job.company}")
    print(f"  Title:       {job.title}")
    print(f"  Status:      {STATUS_DISPLAY.get(job.status, job.status)}")
    print(f"  URL:         {job.url or '-'}")
    print(f"  Location:    {job.location or '-'}")
    print(f"  Salary:      {job.salary or '-'}")
    print(f"  Created:     {job.created_at}")
    print(f"  Applied:     {job.applied_at or '-'}")
    print(f"  Updated:     {job.updated_at}")
    if job.description:
        print(f"  Description: {job.description}")
    if job.notes:
        print(f"  Notes:       {job.notes}")

    # Show cover letters
    letters = get_cover_letters(conn, job.id)
    if letters:
        print(f"\n  Cover letters: {len(letters)}")
        for cl in letters:
            print(f"    - Letter #{cl.id} ({cl.created_at})")


def cmd_job_update(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    if not update_job_field(conn, args.id, args.field, args.value):
        print(f"Job #{args.id} not found.")
        sys.exit(1)
    print(f"Job #{args.id}: updated '{args.field}'.")


def cmd_job_status(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    if not update_job_status(conn, args.id, args.status):
        print(f"Job #{args.id} not found.")
        sys.exit(1)
    print(f"Job #{args.id}: status -> {STATUS_DISPLAY.get(args.status, args.status)}")


def cmd_job_delete(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    if not delete_job(conn, args.id):
        print(f"Job #{args.id} not found.")
        sys.exit(1)
    print(f"Job #{args.id} deleted.")


def cmd_job_apply(args: argparse.Namespace) -> None:
    """Quick-apply: mark as applied and optionally generate a cover letter."""
    conn = get_connection()
    init_db(conn)
    job = get_job(conn, args.id)
    if job is None:
        print(f"Job #{args.id} not found.")
        sys.exit(1)

    update_job_status(conn, args.id, "applied")
    print(f"Job #{args.id} marked as applied: {job.title} at {job.company}")

    if args.cover_letter:
        profile = get_profile(conn)
        if profile is None:
            print("Warning: No profile set up. Skipping cover letter. Run: jobapp profile setup")
            return
        template = args.template or "default"
        content = generate_cover_letter(profile, job, template_name=template)
        cl_id = save_cover_letter(conn, args.id, content)
        print(f"Cover letter #{cl_id} generated and saved.")
        if args.print:
            print("\n" + content)


# ── Cover letter commands ────────────────────────────────────────────────────

def cmd_cover_letter_generate(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    job = get_job(conn, args.job_id)
    if job is None:
        print(f"Job #{args.job_id} not found.")
        sys.exit(1)

    profile = get_profile(conn)
    if profile is None:
        print("No profile set up. Run: jobapp profile setup")
        sys.exit(1)

    template = args.template or "default"
    content = generate_cover_letter(profile, job, template_name=template)

    if args.save:
        cl_id = save_cover_letter(conn, args.job_id, content)
        print(f"Cover letter #{cl_id} saved for job #{args.job_id}.")
    print("\n" + content)


def cmd_cover_letter_list(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    letters = get_cover_letters(conn, args.job_id)
    if not letters:
        print(f"No cover letters for job #{args.job_id}.")
        return
    for cl in letters:
        print(f"--- Cover Letter #{cl.id} (created {cl.created_at}) ---")
        print(cl.content)
        print()


# ── Stats command ────────────────────────────────────────────────────────────

def cmd_stats(args: argparse.Namespace) -> None:
    conn = get_connection()
    init_db(conn)
    stats = get_stats(conn)
    if not stats:
        print("No jobs tracked yet.")
        return
    total = sum(stats.values())
    print("=== Application Stats ===")
    for status, count in sorted(stats.items()):
        label = STATUS_DISPLAY.get(status, status)
        bar = "#" * count
        print(f"  {label:<14} {count:>3}  {bar}")
    print(f"  {'Total':<14} {total:>3}")


# ── Parser ───────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jobapp",
        description="Job Application Helper - track and apply for jobs quickly.",
    )
    sub = parser.add_subparsers(dest="command")

    # ── profile ──
    profile_parser = sub.add_parser("profile", help="Manage your profile/resume info")
    profile_sub = profile_parser.add_subparsers(dest="profile_command")

    profile_sub.add_parser("setup", help="Set up or edit your profile interactively")
    profile_sub.add_parser("show", help="Display your current profile")

    profile_update = profile_sub.add_parser("update", help="Update a single profile field")
    profile_update.add_argument("field", help="Field name to update")
    profile_update.add_argument("value", help="New value")

    # ── job ──
    job_parser = sub.add_parser("job", help="Manage job listings")
    job_sub = job_parser.add_subparsers(dest="job_command")

    job_add = job_sub.add_parser("add", help="Add a new job")
    job_add.add_argument("company", help="Company name")
    job_add.add_argument("title", help="Job title")
    job_add.add_argument("--url", help="Job posting URL")
    job_add.add_argument("--location", help="Job location")
    job_add.add_argument("--salary", help="Salary range")
    job_add.add_argument("--description", help="Job description")
    job_add.add_argument("--notes", help="Personal notes")

    job_list = job_sub.add_parser("list", help="List tracked jobs")
    job_list.add_argument(
        "--status", choices=VALID_STATUSES,
        help="Filter by status",
    )

    job_show = job_sub.add_parser("show", help="Show details for a job")
    job_show.add_argument("id", type=int, help="Job ID")

    job_update = job_sub.add_parser("update", help="Update a job field")
    job_update.add_argument("id", type=int, help="Job ID")
    job_update.add_argument("field", help="Field to update")
    job_update.add_argument("value", help="New value")

    job_status = job_sub.add_parser("status", help="Change a job's status")
    job_status.add_argument("id", type=int, help="Job ID")
    job_status.add_argument("status", choices=VALID_STATUSES, help="New status")

    job_delete = job_sub.add_parser("delete", help="Delete a job")
    job_delete.add_argument("id", type=int, help="Job ID")

    job_apply = job_sub.add_parser("apply", help="Quick-apply: mark as applied")
    job_apply.add_argument("id", type=int, help="Job ID")
    job_apply.add_argument(
        "--cover-letter", action="store_true", dest="cover_letter",
        help="Also generate a cover letter",
    )
    job_apply.add_argument("--template", choices=list(TEMPLATES), help="Cover letter template")
    job_apply.add_argument("--print", action="store_true", help="Print the cover letter")

    # ── cover-letter ──
    cl_parser = sub.add_parser("cover-letter", help="Generate and manage cover letters")
    cl_sub = cl_parser.add_subparsers(dest="cl_command")

    cl_gen = cl_sub.add_parser("generate", help="Generate a cover letter for a job")
    cl_gen.add_argument("job_id", type=int, help="Job ID")
    cl_gen.add_argument("--template", choices=list(TEMPLATES), help="Template name")
    cl_gen.add_argument("--save", action="store_true", help="Save to database")

    cl_list = cl_sub.add_parser("list", help="List saved cover letters for a job")
    cl_list.add_argument("job_id", type=int, help="Job ID")

    # ── stats ──
    sub.add_parser("stats", help="Show application statistics")

    return parser


COMMAND_DISPATCH = {
    ("profile", "setup"): cmd_profile_setup,
    ("profile", "show"): cmd_profile_show,
    ("profile", "update"): cmd_profile_update,
    ("job", "add"): cmd_job_add,
    ("job", "list"): cmd_job_list,
    ("job", "show"): cmd_job_show,
    ("job", "update"): cmd_job_update,
    ("job", "status"): cmd_job_status,
    ("job", "delete"): cmd_job_delete,
    ("job", "apply"): cmd_job_apply,
    ("cover-letter", "generate"): cmd_cover_letter_generate,
    ("cover-letter", "list"): cmd_cover_letter_list,
}


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return

    if args.command == "stats":
        cmd_stats(args)
        return

    sub_command = getattr(args, f"{args.command.replace('-', '_')}_command", None)
    if sub_command is None:
        parser.parse_args([args.command, "--help"])
        return

    handler = COMMAND_DISPATCH.get((args.command, sub_command))
    if handler is None:
        parser.parse_args([args.command, sub_command, "--help"])
        return

    handler(args)


if __name__ == "__main__":
    main()
