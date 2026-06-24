"""Print implementation-log entry scaffolds for spec work."""

from __future__ import annotations

import argparse
from datetime import date


def parse_args() -> argparse.Namespace:
    """Collect the fields that should be stable before writing a log entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Spec ID, for example SPEC-106")
    parser.add_argument("--title", default="Short title", help="Entry title after the spec ID")
    parser.add_argument(
        "--role",
        default="Ingeniero de software",
        choices=["Arquitecto de specs", "Ingeniero de software", "Review agent"],
    )
    parser.add_argument(
        "--status",
        default="Implemented",
        choices=["Planned", "Ready", "Implemented", "Reviewed", "Merged", "Blocked"],
    )
    parser.add_argument("--branch", default="branch-name")
    parser.add_argument("--commit", default="Pending")
    return parser.parse_args()


def main() -> int:
    """Emit a paste-ready template without inventing validation evidence."""
    args = parse_args()
    spec = args.spec.strip().upper()
    print(
        f"""### {date.today().isoformat()} — {spec} — {args.title}

Role: {args.role}
Branch: {args.branch}
Commit/PR: {args.commit}
Status: {args.status}

Summary:
- ...

Validation:
- command: ...: PASS/FAIL/NOT RUN — ...

Review:
- decision: APPROVED/CHANGES_REQUESTED/BLOCKED_BY_SPEC_GAP/N/A

Known gaps:
- None, or list remaining work.
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
