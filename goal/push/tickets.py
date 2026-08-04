"""Slow-test planfile ticketing — extracted from push/core.py.

Writes tickets for genuinely slow tests (and high startup overhead) into
``project/planfile-tickets.yaml``, deduped by a stable ``dedupe_key``.
"""

from typing import Any, Dict, List


def add_slow_test_tickets_to_planfile(test_details: Dict[str, Any]) -> List[str]:
    """Create tasks in project/planfile-tickets.yaml for slow tests."""
    from pathlib import Path
    import yaml
    import os

    planfile_path = Path("project/planfile-tickets.yaml")
    if not planfile_path.exists():
        return []

    try:
        with open(planfile_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return []

    if not isinstance(data, dict):
        data = {}

    if "tickets" not in data or not isinstance(data["tickets"], list):
        data["tickets"] = []

    added_titles = []
    slow_tests = test_details.get("slow_tests", [])

    # Only flag genuinely slow tests. A 0.5s threshold floods the planfile with
    # CLI/integration tests whose time is dominated by interpreter + subprocess
    # startup, not the code under test. 1.0s keeps real outliers, drops the noise.
    THRESHOLD = 1.0

    for test in slow_tests:
        duration = test.get("duration", 0.0)
        if duration < THRESHOLD:
            continue

        classname = test.get("classname", "unknown")
        name = test.get("name", "unknown")

        # Map classname to file
        parts = classname.split(".")
        file_path = "tests"  # fallback
        for i in range(len(parts), 0, -1):
            candidate = "/".join(parts[:i]) + ".py"
            if os.path.exists(candidate):
                file_path = candidate
                break

        title = f"Address slow test: {classname}.{name}"
        dedupe_key = f"test-optimization:{classname}:{name}"

        # Check if ticket already exists
        exists = False
        for ticket in data["tickets"]:
            if isinstance(ticket, dict) and ticket.get("dedupe_key") == dedupe_key:
                exists = True
                break

        if not exists:
            new_ticket = {
                "signal": "slow_test_warning",
                "title": title,
                "description": (
                    f"Test `{classname}.{name}` took {duration:.2f}s to run.\n\n"
                    f"Optimize its setup, mock slow external dependencies, or "
                    f"refactor its logic to reduce overall test suite execution time."
                ),
                "priority": "medium",
                "labels": ["llm-ready", "test-optimization", "slow-test"],
                "files": [file_path],
                "dedupe_key": dedupe_key
            }
            data["tickets"].append(new_ticket)
            added_titles.append(title)

    # Also add a general startup/collection overhead ticket if overhead is high (> 3.0s)
    startup_overhead = test_details.get("startup_overhead", 0.0)
    if startup_overhead > 3.0:
        title = "Address high test suite startup overhead"
        dedupe_key = "test-optimization:general:startup-overhead"
        exists = False
        for ticket in data["tickets"]:
            if isinstance(ticket, dict) and ticket.get("dedupe_key") == dedupe_key:
                exists = True
                break

        if not exists:
            new_ticket = {
                "signal": "slow_test_warning",
                "title": title,
                "description": (
                    f"The test suite startup and collection overhead is high: {startup_overhead:.2f}s.\n\n"
                    f"This overhead is spent on imports, collection, and test environment initialization.\n"
                    f"Analyze fixtures with broad scopes, reduce heavy imports on test collection, "
                    f"and optimize pytest-xdist startup settings to decrease the delay before tests start running."
                ),
                "priority": "high",
                "labels": ["llm-ready", "test-optimization", "startup-overhead"],
                "files": ["pyproject.toml"],
                "dedupe_key": dedupe_key
            }
            data["tickets"].append(new_ticket)
            added_titles.append(title)

    if added_titles:
        try:
            with open(planfile_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        except Exception:
            pass

    return added_titles
