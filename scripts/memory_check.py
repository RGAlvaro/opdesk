"""Validate that spec work has current operational memory before review approval."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_STATE = ROOT / "docs" / "project-state.md"
IMPLEMENTATION_LOG = ROOT / "docs" / "implementation-log.md"


def parse_args() -> argparse.Namespace:
    """Collect the active spec ID and optional strict review expectations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Spec ID, for example SPEC-106")
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Require a reviewed/approved implementation-log entry for the spec.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    """Read a required project memory file with a clear harness error."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"missing required memory file: {path.relative_to(ROOT)}")


def newest_log_entry_for_spec(log_text: str, spec: str) -> str | None:
    """Return the newest implementation-log entry that references the requested spec."""
    entries = re.split(r"(?=^### \d{4}-\d{2}-\d{2} .*$)", log_text, flags=re.MULTILINE)
    for entry in entries:
        if entry.startswith("### ") and spec in entry:
            return entry
    return None


def require(condition: bool, message: str, failures: list[str]) -> None:
    """Accumulate validation failures so the caller sees all memory gaps at once."""
    if not condition:
        failures.append(message)


def main() -> int:
    """Run the memory consistency checks used by review handoff targets."""
    args = parse_args()
    spec = args.spec.strip().upper()
    failures: list[str] = []

    require(
        re.fullmatch(r"SPEC-\d{3}", spec) is not None,
        "SPEC must look like SPEC-106",
        failures,
    )

    project_state = read_text(PROJECT_STATE)
    implementation_log = read_text(IMPLEMENTATION_LOG)
    entry = newest_log_entry_for_spec(implementation_log, spec)

    require(spec in project_state, f"{PROJECT_STATE.relative_to(ROOT)} must mention {spec}", failures)
    require(entry is not None, f"{IMPLEMENTATION_LOG.relative_to(ROOT)} needs an entry for {spec}", failures)

    if entry is not None:
        require("Validation:" in entry, f"latest {spec} log entry must include Validation", failures)
        require("Known gaps:" in entry, f"latest {spec} log entry must include Known gaps", failures)
        require("Branch:" in entry, f"latest {spec} log entry must include Branch", failures)
        require("Status:" in entry, f"latest {spec} log entry must include Status", failures)
        if args.reviewed:
            require("Status: Reviewed" in entry, f"latest {spec} log entry must be Status: Reviewed", failures)
            require(
                "decision: APPROVED" in entry,
                f"latest {spec} log entry must record decision: APPROVED",
                failures,
            )

    if failures:
        print("memory-check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"memory-check passed for {spec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
