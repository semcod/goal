#!/usr/bin/env python3
"""
Slack webhook integration for Goal.

Sends notifications to Slack channel on Goal events.
"""

import os
import sys
import json
import urllib.request
from datetime import datetime


def send_slack_notification(message, commit_info=None):
    """Send notification to Slack."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("⚠ SLACK_WEBHOOK_URL not set")
        return False

    # Build rich message
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🎯 Goal Release"}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Message:*\n{message}"},
                {
                    "type": "mrkdwn",
                    "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
                },
            ],
        },
    ]

    if commit_info:
        blocks.append(
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Commit:*\n`{commit_info.get('hash', 'N/A')[:8]}`",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Author:*\n{commit_info.get('author', 'N/A')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:*\n{commit_info.get('branch', 'N/A')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Version:*\n{commit_info.get('version', 'N/A')}",
                    },
                ],
            }
        )

    payload = {
        "text": message,
        "blocks": blocks,
        "username": "Goal Bot",
        "icon_emoji": ":rocket:",
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
            if response.status == 200:
                print("✓ Slack notification sent")
                return True
            else:
                print(f"✗ Slack error: {response.status}")
                return False

    except Exception as e:
        print(f"✗ Failed to send Slack notification: {e}")
        return False


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: slack-webhook.py 'Message' [commit_hash]")
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

    success = send_slack_notification(message, commit_info)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
