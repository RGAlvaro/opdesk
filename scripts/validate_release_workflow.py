"""Validate the release workflow shape without requiring GitHub Actions locally."""

from __future__ import annotations

from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/production-release.yml")
RELEASE_SCRIPT_PATH = Path("scripts/prod_release.sh")


def require_contains(content: str, needle: str) -> None:
    """Fail fast when a required workflow fragment is absent."""
    if needle not in content:
        raise SystemExit(f"{WORKFLOW_PATH}: missing required fragment: {needle}")


def reject_contains(path: Path, content: str, needle: str) -> None:
    """Fail when a known-unsafe release fragment is present."""
    if needle in content:
        raise SystemExit(f"{path}: unsafe fragment present: {needle}")


def require_order(path: Path, content: str, fragments: list[str]) -> None:
    """Ensure release steps keep their safety-critical ordering."""
    previous_index = -1
    for fragment in fragments:
        index = content.find(fragment)
        if index == -1:
            raise SystemExit(f"{path}: missing required fragment: {fragment}")
        if index <= previous_index:
            raise SystemExit(f"{path}: fragment out of order: {fragment}")
        previous_index = index


def main() -> None:
    """Check the manual deployment workflow for SPEC-307 guardrails."""
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    release_script = RELEASE_SCRIPT_PATH.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        pass
    else:
        workflow = yaml.safe_load(content)
        if not isinstance(workflow, dict):
            raise SystemExit(f"{WORKFLOW_PATH}: workflow YAML did not parse as a mapping")
        if "jobs" not in workflow:
            raise SystemExit(f"{WORKFLOW_PATH}: parsed workflow has no jobs")

    required_fragments = [
        "workflow_dispatch:",
        "target_ref:",
        "deploy_to_production:",
        "make verify",
        "make prod-config",
        "git archive",
        "PROD_SSH_HOST",
        "PROD_SSH_USER",
        "PROD_SSH_PRIVATE_KEY",
        "scripts/prod_release.sh",
        "PROD_PUBLIC_URL",
        "RELEASE_REF",
    ]
    for fragment in required_fragments:
        require_contains(content, fragment)
    for fragment in [
        "start_existing_service postgres",
        "start_existing_service redis",
        "data_services_started=PASS",
        "backend_image_build=PASS",
    ]:
        if fragment not in release_script:
            raise SystemExit(f"{RELEASE_SCRIPT_PATH}: missing required fragment: {fragment}")
    require_order(
        RELEASE_SCRIPT_PATH,
        release_script,
        [
            "backup=PASS",
            "build backend",
            "backend_image_build=PASS",
            "poetry run alembic upgrade head",
            "migrations=PASS",
            "up -d --build",
            "compose_update=PASS",
        ],
    )
    reject_contains(RELEASE_SCRIPT_PATH, release_script, "up -d postgres redis")
    print(f"{WORKFLOW_PATH}: release workflow static validation passed")


if __name__ == "__main__":
    main()
