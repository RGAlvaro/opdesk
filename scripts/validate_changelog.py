"""Validate repository release notes for production deployment safety."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CHANGELOG_PATH = Path("CHANGELOG.md")
ENTRY_PATTERN = re.compile(r"^## (?P<date>\d{4}-\d{2}-\d{2}) - (?P<title>.+)$")
SECTION_PATTERN = re.compile(r"^### (?P<section>.+)$")
ALLOWED_SECTIONS = {"Added", "Changed", "Fixed"}
SECRET_PATTERNS = [
    re.compile(r"password\s*[:=]", re.IGNORECASE),
    re.compile(r"secret\s*[:=]", re.IGNORECASE),
    re.compile(r"token\s*[:=]", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
]


@dataclass(frozen=True)
class ChangelogEntry:
    """Represent one validated changelog release entry."""

    heading: str
    release_date: date
    sections: dict[str, list[str]]


def parse_changelog(content: str) -> list[ChangelogEntry]:
    """Parse and validate the changelog heading, order, sections, and bullets."""
    lines = content.splitlines()
    if not lines or lines[0] != "# Changelog":
        raise ValueError("CHANGELOG.md must start with '# Changelog'.")

    entries: list[ChangelogEntry] = []
    current_heading: str | None = None
    current_date: date | None = None
    current_sections: dict[str, list[str]] = {}
    current_section: str | None = None

    def finish_entry() -> None:
        """Store the current entry after checking it contains useful notes."""
        nonlocal current_heading, current_date, current_sections, current_section
        if current_heading is None or current_date is None:
            return
        if not current_sections:
            raise ValueError(f"{current_heading}: entry must include at least one section.")
        empty_sections = [
            section for section, bullets in current_sections.items() if not bullets
        ]
        if empty_sections:
            raise ValueError(
                f"{current_heading}: empty section(s): {', '.join(empty_sections)}."
            )
        entries.append(
            ChangelogEntry(
                heading=current_heading,
                release_date=current_date,
                sections=current_sections,
            )
        )
        current_heading = None
        current_date = None
        current_sections = {}
        current_section = None

    for line_number, line in enumerate(lines[1:], start=2):
        if line.startswith("## "):
            finish_entry()
            match = ENTRY_PATTERN.match(line)
            if match is None:
                raise ValueError(
                    f"line {line_number}: release heading must use "
                    "'## YYYY-MM-DD - Title'."
                )
            current_heading = line.removeprefix("## ")
            current_date = date.fromisoformat(match.group("date"))
            current_sections = {}
            current_section = None
            continue

        if line.startswith("### "):
            if current_heading is None:
                raise ValueError(f"line {line_number}: section appears before an entry.")
            section_match = SECTION_PATTERN.match(line)
            section = section_match.group("section") if section_match else ""
            if section not in ALLOWED_SECTIONS:
                raise ValueError(
                    f"line {line_number}: unsupported section '{section}'."
                )
            if section in current_sections:
                raise ValueError(
                    f"line {line_number}: duplicate section '{section}'."
                )
            current_sections[section] = []
            current_section = section
            continue

        if line.startswith("- "):
            if current_section is None:
                raise ValueError(f"line {line_number}: bullet appears before a section.")
            current_sections[current_section].append(line)
            continue

        if line.strip() == "":
            continue

        raise ValueError(f"line {line_number}: unsupported changelog content.")

    finish_entry()

    if not entries:
        raise ValueError("CHANGELOG.md must include at least one release entry.")
    release_dates = [entry.release_date for entry in entries]
    if release_dates != sorted(release_dates, reverse=True):
        raise ValueError("release entries must be newest-first by heading date.")
    return entries


def reject_secret_like_content(content: str) -> None:
    """Fail when changelog text looks like it contains credentials."""
    for pattern in SECRET_PATTERNS:
        if pattern.search(content):
            raise ValueError("CHANGELOG.md contains secret-like content.")


def main() -> None:
    """Run changelog validation for local checks and production workflows."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--entry",
        help="Release heading without leading ##, for example '2026-08-12 - Production Release'.",
    )
    args = parser.parse_args()

    content = CHANGELOG_PATH.read_text(encoding="utf-8")
    reject_secret_like_content(content)
    entries = parse_changelog(content)
    if args.entry and args.entry not in {entry.heading for entry in entries}:
        raise SystemExit(f"{CHANGELOG_PATH}: missing release entry: {args.entry}")
    print(f"{CHANGELOG_PATH}: changelog validation passed")


if __name__ == "__main__":
    main()
