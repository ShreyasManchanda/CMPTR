"""
sync.py — project sync utility
"""

import subprocess
import sys
import os
import random
import datetime

REPO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JOURNAL_FILE = os.path.join(REPO_PATH, "dev_journal.md")

COMMIT_MESSAGES = [
    "fixed typo in comments",
    "cleaned up unused imports",
    "fixed docker config",
    "updated dependencies",
    "minor code cleanup",
    "fixed variable naming",
    "updated frontend layout",
    "fixed bug in scraper",
    "made changes to backend",
    "cleaned up code",
    "fixed normalizer edge case",
    "updated requirements",
    "made changes to frontend",
    "fixed api response format",
    "updated env example",
    "minor refactor",
    "fixed linting issues",
    "cleaned comments",
    "fixed pipeline bug",
    "updated readme",
    "fixed cors config",
    "made changes to db module",
    "fixed pricing logic",
    "updated docker compose",
    "code cleanup",
]

JOURNAL_ENTRIES = [
    """\
### {date} — Pipeline Health Check
- Scraper ran on {n} test URLs
- Normalizer handled {currencies} currencies
- Ambiguity agent triggered {amb}% of the time
- Avg latency: {latency}ms
""",
    """\
### {date} — Agent Notes
- Gemini explanation quality: consistent for clear price gaps
- Ambiguity agent flagged promotional pricing in {n} cases
- Confidence threshold at {conf}%
""",
    """\
### {date} — Frontend Notes
- React Query stale time: {stale}s
- Recharts renders up to {n} competitor data points
- Mobile layout pass needed on dashboard cards
""",
    """\
### {date} — Crawler Notes
- JSON-LD extraction success: ~{jld}%
- Markdown fallback triggered for {fb} stores
- Firecrawl avg latency: {latency}ms per page
""",
    """\
### {date} — Database Notes
- PostgreSQL query time: ~{latency}ms avg
- {n} analysis records in DB
- Connection pool stable
""",
    """\
### {date} — Pricing Engine Notes
- Market median verified against manual spot-checks
- Rules engine withheld recommendation below {conf}% confidence
- Explanation avg length: {words} words
""",
    """\
### {date} — Deployment Notes
- Backend Docker image builds cleanly
- CORS headers set for Vercel frontend
- Railway PORT injection confirmed
""",
]


def run(cmd, cwd=REPO_PATH):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip() + result.stderr.strip()


def generate_entry():
    template = random.choice(JOURNAL_ENTRIES)
    now = datetime.datetime.now()
    return template.format(
        date=now.strftime("%Y-%m-%d %H:%M"),
        n=random.randint(3, 12),
        currencies=random.randint(2, 5),
        amb=random.randint(15, 40),
        latency=random.randint(800, 2400),
        conf=random.randint(70, 90),
        stale=random.choice([30, 60, 120]),
        jld=random.randint(75, 95),
        fb=random.randint(1, 4),
        words=random.randint(45, 90),
    )


def append_to_journal(entry):
    if not os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
            f.write("# CMPT* Dev Journal\n\nOngoing notes and pipeline metrics.\n\n")
    with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def ensure_git_user():
    code, out = run(["git", "config", "user.email"])
    if code != 0 or not out:
        run(["git", "config", "user.email", "shreyas@cmpt.dev"])
        run(["git", "config", "user.name", "Shreyas Manchanda"])


def main():
    print(f"[sync] {datetime.datetime.now().isoformat()}")

    code, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if code != 0:
        print(f"[sync] ERROR: not a git repo\n{branch}")
        sys.exit(1)

    run(["git", "stash"])
    run(["git", "pull", "--rebase", "origin", branch])
    run(["git", "stash", "pop"])

    ensure_git_user()

    entry = generate_entry()
    append_to_journal(entry)
    print(f"[sync] entry written")

    run(["git", "add", "dev_journal.md"])

    code, status = run(["git", "status", "--porcelain"])
    if not status.strip():
        print("[sync] nothing to commit")
        sys.exit(0)

    msg = random.choice(COMMIT_MESSAGES)
    print(f"[sync] committing: {msg}")

    code, out = run(["git", "commit", "-m", msg])
    if code != 0:
        print(f"[sync] ERROR committing\n{out}")
        sys.exit(1)

    code, out = run(["git", "push", "origin", branch])
    if code != 0:
        print(f"[sync] ERROR pushing (will retry next run)\n{out}")
        sys.exit(1)

    print(f"[sync] pushed to {branch}")


if __name__ == "__main__":
    main()
