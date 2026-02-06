# Job Application Helper

A command-line tool to track job applications, manage your profile, and generate cover letters quickly.

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# 1. Set up your profile
jobapp profile setup

# 2. Add a job
jobapp job add "Acme Corp" "Software Engineer" --url "https://acme.com/jobs/123" --location "Remote"

# 3. Quick-apply with a cover letter
jobapp job apply 1 --cover-letter --print

# 4. Check your stats
jobapp stats
```

## Commands

### Profile Management

| Command | Description |
|---|---|
| `jobapp profile setup` | Interactive profile setup (name, email, skills, experience, etc.) |
| `jobapp profile show` | Display your saved profile |
| `jobapp profile update <field> <value>` | Update a single field (e.g., `skills`, `email`) |

### Job Tracking

| Command | Description |
|---|---|
| `jobapp job add <company> <title>` | Add a job (optional: `--url`, `--location`, `--salary`, `--description`, `--notes`) |
| `jobapp job list` | List all tracked jobs (optional: `--status <status>`) |
| `jobapp job show <id>` | Show full details for a job |
| `jobapp job update <id> <field> <value>` | Update a job field |
| `jobapp job status <id> <status>` | Change job status |
| `jobapp job delete <id>` | Delete a job |
| `jobapp job apply <id>` | Quick-apply (optional: `--cover-letter`, `--template`, `--print`) |

**Statuses:** `saved`, `applied`, `phone_screen`, `interview`, `offer`, `rejected`, `withdrawn`

### Cover Letters

| Command | Description |
|---|---|
| `jobapp cover-letter generate <job_id>` | Generate a cover letter (optional: `--template`, `--save`) |
| `jobapp cover-letter list <job_id>` | List saved cover letters for a job |

**Templates:** `default` (full letter), `concise` (brief format)

### Stats

```bash
jobapp stats
```

Shows a breakdown of all your applications by status.

## Data Storage

Data is stored in a SQLite database at `~/.jobapp/jobs.db`. Set `JOBAPP_DB_PATH` to use a custom location.

## Running Tests

```bash
python -m unittest tests.test_app -v
```
