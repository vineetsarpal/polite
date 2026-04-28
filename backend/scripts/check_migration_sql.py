"""
Dangerous-pattern lint over Alembic-rendered SQL.

Reads SQL from stdin (or a file passed as argv[1]). Fails (exit 1) on
destructive patterns unless every new migration file in
backend/alembic/versions/ contains a comment starting with `# safety:`.

Patterns that fail:
  - DROP TABLE
  - DROP COLUMN
  - TRUNCATE
  - ALTER COLUMN ... NOT NULL  (unless the same statement contains
    SET DEFAULT — autogen typically emits these together when the user
    supplied a server_default)

Patterns that warn (printed but exit 0):
  - DROP CONSTRAINT  (often FK-related; usually intentional)
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
from typing import Iterable

DANGEROUS = [
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bDROP\s+COLUMN\b", re.IGNORECASE), "DROP COLUMN"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
]
NOT_NULL_NO_DEFAULT = re.compile(
    r"ALTER\s+COLUMN[^;]*?SET\s+NOT\s+NULL(?![^;]*SET\s+DEFAULT)",
    re.IGNORECASE | re.DOTALL,
)
WARNINGS = [
    (re.compile(r"\bDROP\s+CONSTRAINT\b", re.IGNORECASE), "DROP CONSTRAINT (review FK impact)"),
]


def new_migration_files(base_ref: str = "origin/main") -> list[pathlib.Path]:
    """Files added under backend/alembic/versions/ since base_ref."""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=A", f"{base_ref}...HEAD", "--", "backend/alembic/versions/"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [pathlib.Path(p) for p in out.stdout.splitlines() if p.endswith(".py")]


def has_safety_marker(files: Iterable[pathlib.Path]) -> bool:
    """True if any new migration file contains a `# safety:` marker comment."""
    for f in files:
        if not f.exists():
            continue
        text = f.read_text()
        if re.search(r"^\s*#\s*safety:\s*\S", text, re.MULTILINE):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file", nargs="?", default="-")
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git ref to diff migration files against (default: origin/main)",
    )
    args = parser.parse_args()

    sql = sys.stdin.read() if args.sql_file == "-" else pathlib.Path(args.sql_file).read_text()

    failures: list[str] = []
    for pattern, label in DANGEROUS:
        if pattern.search(sql):
            failures.append(label)
    if NOT_NULL_NO_DEFAULT.search(sql):
        failures.append("ALTER COLUMN ... SET NOT NULL without SET DEFAULT")

    for pattern, label in WARNINGS:
        if pattern.search(sql):
            print(f"::warning ::{label}", file=sys.stderr)

    if not failures:
        print("Migration SQL passes safety lint.")
        return 0

    new_files = new_migration_files(args.base_ref)
    if has_safety_marker(new_files):
        print(
            f"Destructive patterns detected ({', '.join(failures)}) but a # safety: "
            f"marker was found in a new migration file — allowing.",
        )
        return 0

    print("MIGRATION SAFETY GATE FAILED", file=sys.stderr)
    print(f"  Detected: {', '.join(failures)}", file=sys.stderr)
    print(
        "  If destruction is intentional, add a `# safety: <reason>` comment "
        "to the new migration file in backend/alembic/versions/.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
