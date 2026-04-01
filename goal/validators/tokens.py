"""Token detection for security validation."""
import re
from typing import List, Tuple, Optional


# Ordered list of (pattern_substring, token_label) for classifying detected tokens.
# First match wins; order matters (e.g. 'sk-or-v1' before 'sk-').
_TOKEN_TYPE_HINTS = [
    ('ghp_',     "GitHub Personal Access"),
    ('gho_',     "GitHub Personal Access"),
    ('ghu_',     "GitHub Personal Access"),
    ('AKIA',     "AWS Access Key"),
    ('sk-or-v1', "OpenRouter API"),
    ('sk-',      "Stripe API"),
    ('xoxb',     "Slack Bot"),
    ('xoxp',     "Slack User"),
    ('glpat',    "GitLab"),
    ('Bearer',   "Bearer Token"),
    ('Token',    "API Token"),
]


def _classify_token(pattern: str) -> str:
    """Return a human-readable token type label for a pattern."""
    for hint, label in _TOKEN_TYPE_HINTS:
        if hint in pattern:
            return label
    return "API Key"


def detect_tokens_in_content(content: str, patterns: List[str]) -> List[Tuple[str, Optional[int]]]:
    """Detect tokens in file content using regex patterns.

    Returns:
        List of (token_type, line_number) tuples
    """
    detected = []
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            try:
                # Check if pattern is marked as case-sensitive with 'CS:' prefix
                if pattern.startswith('CS:'):
                    actual_pattern = pattern[3:]
                    match = re.search(actual_pattern, line)
                else:
                    match = re.search(pattern, line, re.IGNORECASE)

                if match:
                    detected.append((_classify_token(pattern), line_num))
                    # Only report first match per line to avoid spam
                    break
            except re.error:
                continue

    return detected


def get_default_token_patterns() -> List[str]:
    """Return default regex patterns for token detection."""
    return [
        r'ghp_[a-zA-Z0-9]{36}',
        r'gho_[a-zA-Z0-9]{36}',
        r'ghu_[a-zA-Z0-9]{36}',
        r'ghs_[a-zA-Z0-9]{36}',
        r'ghr_[a-zA-Z0-9]{36}',
        r'AKIA[0-9A-Z]{16}',
        r'sk-[a-zA-Z0-9]{48}',
        r'xoxb-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}',
        r'xoxp-[0-9]{13}-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}',
        r'glpat-[a-zA-Z0-9_-]{20}',
        r'pk_live_[a-zA-Z0-9]{24}',
        r'pk_test_[a-zA-Z0-9]{24}',
        r'sk_live_[a-zA-Z0-9]{24}',
        r'sk_test_[a-zA-Z0-9]{24}',
        r'sk-or-v1-(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9_-]{32,}',
        r'CS:^[A-Z][A-Z0-9_]{5,}=(?=(?:.*[a-z]))(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9_-]{20,}',
        r'\bBearer\s+(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[a-zA-Z0-9_-]{32,}\b',
        r'\bToken\s+(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[a-zA-Z0-9_-]{32,}\b',
        r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
        r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----',
        r'-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----',
        r'-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----',
        r'CS:^[A-Z][A-Z0-9_]+=(?=(?:.*[a-z]))(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9_-]{20,}',
    ]
