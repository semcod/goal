#!/usr/bin/env python3
"""
Discord webhook integration for Goal.

Sends notifications to Discord channel on Goal events.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime


def send_discord_notification(message, commit_info=None):
    """Send notification to Discord."""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("⚠ DISCORD_WEBHOOK_URL not set")
        return False

    # Build embed
    embed = {
        "title": "🎯 Goal Release",
        "description": message,
        "color": 0x00FF00,  # Green
        "timestamp": datetime.now().isoformat(),
        "footer": {"text": "Goal Automation"},
    }

    if commit_info:
        embed["fields"] = [
            {
                "name": "Commit",
                "value": f"`{commit_info.get('hash', 'N/A')[:8]}`",
                "inline": True,
            },
            {
                "name": "Author",
                "value": commit_info.get("author", "N/A"),
                "inline": True,
            },
            {
                "name": "Branch",
                "value": commit_info.get("branch", "N/A"),
                "inline": True,
            },
            {
                "name": "Version",
                "value": commit_info.get("version", "N/A"),
                "inline": True,
            },
        ]

    payload = {
        "content": None,
        "embeds": [embed],
        "username": "Goal Bot",
        "avatar_url": "https://cdn.jsdelivr.net/gh/wronai/goal@main/docs/logo.png",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Goal-Webhook/1.0",
            },
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status in [200, 204]:
                print("✓ Discord notification sent")
                return True
            else:
                print(f"✗ Discord error: {response.status}")
                return False

    except Exception as e:
        print(f"✗ Failed to send Discord notification: {e}")
        return False


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: discord-webhook.py 'Message' [commit_hash]")
        sys.exit(1)

    message = sys.argv[1]

    commit_info = None
    if len(sys.argv) > 2:
        commit_info = {
            "hash": sys.argv[2],
            "author": os.environ.get("GIT_AUTHOR_NAME", "Unknown"),
            "branch": os.environ.get("GIT_BRANCH", "main"),
            "version": os.environ.get("VERSION", "N/A"),
        }

    success = send_discord_notification(message, commit_info)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
