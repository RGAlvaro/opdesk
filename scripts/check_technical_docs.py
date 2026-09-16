"""Validate that the technical documentation tracks core architecture facts."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TECH_DOC = ROOT / "docs" / "technical-documentation.md"
ALEMBIC_DIR = ROOT / "backend" / "alembic" / "versions"
COMPOSE_FILES = [ROOT / "docker-compose.yml", ROOT / "docker-compose.prod.yml"]

REQUIRED_SECTIONS = [
    "## 3. Technology Stack",
    "## 4. Runtime Architecture",
    "## 5. Backend Architecture",
    "## 6. Database Model",
    "## 7. API Surface",
    "## 9. Frontend Architecture",
    "## 10. Background Jobs And Notifications",
    "## 12. Security Model",
    "## 13. Deployment And Release Process",
    "## 18. PDF Strategy",
]

REQUIRED_TERMS = [
    "FastAPI",
    "React",
    "TypeScript",
    "PostgreSQL",
    "Redis",
    "Celery",
    "Celery beat",
    "Alembic",
    "Docker Compose",
    "Caddy",
    "Playwright",
    "Resend",
]


def read(path: Path) -> str:
    """Read one required repository file as UTF-8."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"missing required file: {path.relative_to(ROOT)}") from exc


def alembic_heads() -> set[str]:
    """Return Alembic head revision ids from version files."""
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in ALEMBIC_DIR.glob("*.py"):
        content = read(path)
        revision_match = re.search(r'^revision:\s*str\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if revision_match is None:
            continue
        revisions.add(revision_match.group(1))
        parent_match = re.search(
            r'^down_revision:\s*str\s*\|\s*None\s*=\s*"([^"]+)"',
            content,
            re.MULTILINE,
        )
        if parent_match is not None:
            parents.add(parent_match.group(1))
    return revisions - parents


def compose_services(path: Path) -> set[str]:
    """Parse top-level service names from a simple Compose file."""
    services: set[str] = set()
    in_services = False
    for line in read(path).splitlines():
        if line == "services:":
            in_services = True
            continue
        if in_services and line and not line.startswith(" "):
            break
        if in_services:
            match = re.match(r"^  ([A-Za-z0-9_-]+):$", line)
            if match is not None:
                services.add(match.group(1))
    return services


def require(condition: bool, message: str, failures: list[str]) -> None:
    """Collect validation failures so callers can fix all stale areas at once."""
    if not condition:
        failures.append(message)


def main() -> int:
    """Validate documentation coverage for current runtime and architecture facts."""
    content = read(TECH_DOC)
    failures: list[str] = []

    require(
        re.search(r"^Last updated: \d{4}-\d{2}-\d{2}$", content, re.MULTILINE) is not None,
        "technical documentation must include a YYYY-MM-DD Last updated line",
        failures,
    )
    for section in REQUIRED_SECTIONS:
        require(section in content, f"missing required section: {section}", failures)
    for term in REQUIRED_TERMS:
        require(term in content, f"missing required technology term: {term}", failures)

    heads = alembic_heads()
    require(len(heads) == 1, f"expected exactly one Alembic head, found {sorted(heads)}", failures)
    for head in heads:
        require(head in content, f"technical documentation must mention Alembic head {head}", failures)

    for compose_file in COMPOSE_FILES:
        for service in sorted(compose_services(compose_file)):
            require(
                f"`{service}`" in content,
                f"technical documentation must mention Compose service `{service}` from "
                f"{compose_file.relative_to(ROOT)}",
                failures,
            )

    try:
        content.encode("ascii")
    except UnicodeEncodeError:
        failures.append("technical documentation must stay ASCII for predictable PDF conversion")

    if failures:
        print("technical-docs-check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("technical-docs-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
