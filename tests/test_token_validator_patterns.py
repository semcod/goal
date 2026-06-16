"""Regression tests for goal.yaml token-detection patterns."""

from goal.validators.tokens import (
    detect_tokens_in_content,
    get_default_token_patterns,
    migrate_token_patterns,
    resolve_token_patterns,
)


LEGACY_PATTERNS = [
    r"^[A-Z_]+=[a-zA-Z0-9_-]{20,}",
    r"Bearer\s+[a-zA-Z0-9_-]{20,}",
]


def test_urisys_nightly_session_env_is_not_flagged() -> None:
    snippet = (
        "URISYS_NIGHTLY_SESSIONS=urisys-node-docker-gui "
        "bash scripts/run-lab-nightly.sh"
    )
    assert detect_tokens_in_content(snippet, get_default_token_patterns()) == []
    assert detect_tokens_in_content(snippet, resolve_token_patterns(LEGACY_PATTERNS)) == []


def test_legacy_patterns_are_removed_on_resolve() -> None:
    resolved = resolve_token_patterns(LEGACY_PATTERNS)
    assert r"^[A-Z_]+=[a-zA-Z0-9_-]{20,}" not in resolved
    assert any("API|KEY|TOKEN" in pattern for pattern in resolved)


def test_migrate_token_patterns_reports_changes() -> None:
    migrated, changed = migrate_token_patterns(LEGACY_PATTERNS)
    assert changed is True
    assert r"^[A-Z_]+=[a-zA-Z0-9_-]{20,}" not in migrated


def test_credential_env_assignments_are_still_flagged() -> None:
    snippet = "API_KEY=Abcdef12345678901234567890abcdef123456789"
    assert detect_tokens_in_content(snippet, get_default_token_patterns())
