#!/usr/bin/env python3
"""
Post-commit hook example for Goal.

Sends notifications and updates external systems after commit.
"""

import sys
import os
import subprocess
import json
from datetime import datetime


def get_commit_info():
    """Get information about the last commit."""
    # Get commit hash
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%H"], capture_output=True, text=True
    )
    commit_hash = result.stdout.strip()

    # Get commit message
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"], capture_output=True, text=True
    )
    commit_msg = result.stdout.strip()

    # Get author
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%an"], capture_output=True, text=True
    )
    author = result.stdout.strip()

    # Get branch
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    branch = result.stdout.strip()

    return {
        "hash": commit_hash[:8],
        "message": commit_msg,
        "author": author,
        "branch": branch,
        "timestamp": datetime.now().isoformat(),
    }


def notify_slack(info):
    """Send Slack notification."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return

    try:
        import urllib.request

        payload = {
            "text": f"New commit on {info['branch']}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*New Commit*\n`{info['hash']}` {info['message'][:50]}...\n*Author:* {info['author']}",
                    },
                }
            ],
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            webhook_url, data=data, headers={"Content-Type": "application/json"}
        )

        urllib.request.urlopen(req, timeout=10)
        print("  ✓ Slack notification sent")
    except Exception as e:
        print(f"  ⚠ Slack notification failed: {e}")


def update_changelog(info):
    """Auto-update changelog with commit info."""
    changelog_path = "CHANGELOG.md"
    if not os.path.exists(changelog_path):
        return

    try:
        with open(changelog_path, "r") as f:
            content = f.read()

        # Add entry under ## Unreleased
        entry = f"- {info['message']} ({info['hash']})\n"

        if "## Unreleased" in content:
            content = content.replace("## Unreleased\n", f"## Unreleased\n\n{entry}")

            with open(changelog_path, "w") as f:
                f.write(content)

            print("  ✓ CHANGELOG.md updated")
    except Exception as e:
        print(f"  ⚠ Could not update changelog: {e}")


def log_to_file(info):
    """Log commit to local file."""
    log_file = ".goal/commit.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "a") as f:
        f.write(
            f"{info['timestamp']} | {info['hash']} | {info['message'][:50]} | {info['author']}\n"
        )

    print("  ✓ Commit logged")


def main():
    """Run post-commit actions."""
    print("🎉 Running post-commit hooks...")

    # Get commit info
    info = get_commit_info()
    print(f"\nCommit: {info['hash']} on {info['branch']}")
    print(f"Message: {info['message'][:60]}...")

    # Run actions
    print("\n1. Sending notifications...")
    notify_slack(info)

    print("\n2. Updating changelog...")
    update_changelog(info)

    print("\n3. Logging commit...")
    log_to_file(info)

    print("\n✅ Post-commit hooks completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
