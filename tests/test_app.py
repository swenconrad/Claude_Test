"""Tests for the Job Application Helper."""

import os
import sqlite3
import tempfile
import unittest

from job_app_helper.cover_letter import (
    generate_cover_letter,
    get_cover_letters,
    save_cover_letter,
)
from job_app_helper.database import get_connection, init_db
from job_app_helper.jobs import (
    add_job,
    delete_job,
    get_job,
    get_stats,
    list_jobs,
    update_job_field,
    update_job_status,
)
from job_app_helper.profile import Profile, get_profile, save_profile, update_profile_field


class DBTestCase(unittest.TestCase):
    """Base test case that creates a temporary database for each test."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.environ["JOBAPP_DB_PATH"] = self.tmp.name
        self.conn = get_connection()
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.tmp.name)
        os.environ.pop("JOBAPP_DB_PATH", None)


class TestProfile(DBTestCase):
    def test_no_profile_initially(self):
        self.assertIsNone(get_profile(self.conn))

    def test_save_and_get_profile(self):
        p = Profile(full_name="Jane Doe", email="jane@example.com", phone="555-1234")
        save_profile(self.conn, p)
        loaded = get_profile(self.conn)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.full_name, "Jane Doe")
        self.assertEqual(loaded.email, "jane@example.com")
        self.assertEqual(loaded.phone, "555-1234")

    def test_update_profile_field(self):
        p = Profile(full_name="Jane Doe", email="jane@example.com")
        save_profile(self.conn, p)
        self.assertTrue(update_profile_field(self.conn, "phone", "555-9999"))
        loaded = get_profile(self.conn)
        self.assertEqual(loaded.phone, "555-9999")

    def test_update_profile_field_invalid(self):
        with self.assertRaises(ValueError):
            update_profile_field(self.conn, "nonexistent", "value")

    def test_update_profile_no_profile(self):
        self.assertFalse(update_profile_field(self.conn, "email", "x@y.com"))

    def test_save_profile_overwrites(self):
        p1 = Profile(full_name="Jane", email="jane@example.com")
        save_profile(self.conn, p1)
        p2 = Profile(full_name="Jane Updated", email="jane2@example.com")
        save_profile(self.conn, p2)
        loaded = get_profile(self.conn)
        self.assertEqual(loaded.full_name, "Jane Updated")
        self.assertEqual(loaded.email, "jane2@example.com")


class TestJobs(DBTestCase):
    def test_add_and_get_job(self):
        job_id = add_job(self.conn, company="Acme", title="Engineer")
        job = get_job(self.conn, job_id)
        self.assertIsNotNone(job)
        self.assertEqual(job.company, "Acme")
        self.assertEqual(job.title, "Engineer")
        self.assertEqual(job.status, "saved")

    def test_list_jobs_empty(self):
        self.assertEqual(list_jobs(self.conn), [])

    def test_list_jobs_with_filter(self):
        add_job(self.conn, company="A", title="Dev")
        j2 = add_job(self.conn, company="B", title="PM")
        update_job_status(self.conn, j2, "applied")
        self.assertEqual(len(list_jobs(self.conn, status="saved")), 1)
        self.assertEqual(len(list_jobs(self.conn, status="applied")), 1)

    def test_update_job_status(self):
        job_id = add_job(self.conn, company="X", title="Y")
        self.assertTrue(update_job_status(self.conn, job_id, "applied"))
        job = get_job(self.conn, job_id)
        self.assertEqual(job.status, "applied")
        self.assertIsNotNone(job.applied_at)

    def test_update_job_status_invalid(self):
        job_id = add_job(self.conn, company="X", title="Y")
        with self.assertRaises(ValueError):
            update_job_status(self.conn, job_id, "invalid_status")

    def test_update_job_field(self):
        job_id = add_job(self.conn, company="X", title="Y")
        self.assertTrue(update_job_field(self.conn, job_id, "salary", "$100k"))
        job = get_job(self.conn, job_id)
        self.assertEqual(job.salary, "$100k")

    def test_update_job_field_invalid(self):
        job_id = add_job(self.conn, company="X", title="Y")
        with self.assertRaises(ValueError):
            update_job_field(self.conn, job_id, "bad_field", "value")

    def test_delete_job(self):
        job_id = add_job(self.conn, company="X", title="Y")
        self.assertTrue(delete_job(self.conn, job_id))
        self.assertIsNone(get_job(self.conn, job_id))

    def test_delete_nonexistent_job(self):
        self.assertFalse(delete_job(self.conn, 999))

    def test_get_stats(self):
        add_job(self.conn, company="A", title="1")
        add_job(self.conn, company="B", title="2")
        j3 = add_job(self.conn, company="C", title="3")
        update_job_status(self.conn, j3, "applied")
        stats = get_stats(self.conn)
        self.assertEqual(stats["saved"], 2)
        self.assertEqual(stats["applied"], 1)

    def test_get_nonexistent_job(self):
        self.assertIsNone(get_job(self.conn, 999))


class TestCoverLetter(DBTestCase):
    def _setup_profile_and_job(self):
        p = Profile(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="555-1234",
            summary="Experienced software engineer with 5 years in Python.",
            skills="Python, SQL, Git",
            experience="- Led a team of 5 engineers building data pipelines",
        )
        save_profile(self.conn, p)
        job_id = add_job(self.conn, company="TechCorp", title="Senior Developer")
        return p, get_job(self.conn, job_id)

    def test_generate_default_cover_letter(self):
        profile, job = self._setup_profile_and_job()
        letter = generate_cover_letter(profile, job)
        self.assertIn("TechCorp", letter)
        self.assertIn("Senior Developer", letter)
        self.assertIn("Jane Doe", letter)
        self.assertIn("Python, SQL, Git", letter)

    def test_generate_concise_cover_letter(self):
        profile, job = self._setup_profile_and_job()
        letter = generate_cover_letter(profile, job, template_name="concise")
        self.assertIn("TechCorp", letter)
        self.assertIn("Jane Doe", letter)
        self.assertNotIn("Dear Hiring Manager,\n\nI am writing to express", letter)

    def test_generate_invalid_template(self):
        profile, job = self._setup_profile_and_job()
        with self.assertRaises(ValueError):
            generate_cover_letter(profile, job, template_name="nonexistent")

    def test_save_and_list_cover_letters(self):
        _, job = self._setup_profile_and_job()
        cl_id = save_cover_letter(self.conn, job.id, "Test content")
        letters = get_cover_letters(self.conn, job.id)
        self.assertEqual(len(letters), 1)
        self.assertEqual(letters[0].id, cl_id)
        self.assertEqual(letters[0].content, "Test content")

    def test_no_cover_letters(self):
        _, job = self._setup_profile_and_job()
        self.assertEqual(get_cover_letters(self.conn, job.id), [])

    def test_cover_letters_deleted_with_job(self):
        _, job = self._setup_profile_and_job()
        save_cover_letter(self.conn, job.id, "Letter content")
        delete_job(self.conn, job.id)
        self.assertEqual(get_cover_letters(self.conn, job.id), [])


class TestCLIParsing(unittest.TestCase):
    """Test that the CLI parser accepts expected arguments."""

    def test_parser_job_add(self):
        from job_app_helper.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["job", "add", "Acme", "Developer", "--url", "https://acme.com"])
        self.assertEqual(args.company, "Acme")
        self.assertEqual(args.title, "Developer")
        self.assertEqual(args.url, "https://acme.com")

    def test_parser_job_list_status(self):
        from job_app_helper.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["job", "list", "--status", "applied"])
        self.assertEqual(args.status, "applied")

    def test_parser_stats(self):
        from job_app_helper.cli import build_parser
        parser = build_parser()
        args = parser.parse_args(["stats"])
        self.assertEqual(args.command, "stats")


if __name__ == "__main__":
    unittest.main()
