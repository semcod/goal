"""Token detection for security validation with entropy-based filtering."""

import re
import math
from typing import List, Tuple, Optional, Set


# Ordered list of (pattern_substring, token_label) for classifying detected tokens.
# First match wins; order matters (e.g. 'sk-or-v1' before 'sk-').
_TOKEN_TYPE_HINTS = [
    ("ghp_", "GitHub Personal Access"),
    ("gho_", "GitHub Personal Access"),
    ("ghu_", "GitHub Personal Access"),
    ("AKIA", "AWS Access Key"),
    ("sk-or-v1", "OpenRouter API"),
    ("sk-", "Stripe API"),
    ("xoxb", "Slack Bot"),
    ("xoxp", "Slack User"),
    ("glpat", "GitLab"),
    ("Bearer", "Bearer Token"),
    ("Token", "API Token"),
]


# Entropy thresholds per token type (Shannon entropy bits per character)
# Real secrets should have high entropy (>3.5 bits/char)
# Dummy values like "xxx", "abc123" have low entropy (<2.5 bits/char)
_ENTROPY_THRESHOLDS = {
    "default": 3.0,
    "GitHub Personal Access": 3.2,
    "AWS Access Key": 3.0,
    "OpenRouter API": 3.5,
    "Stripe API": 3.5,
    "Slack Bot": 3.0,
    "Slack User": 3.0,
    "GitLab": 3.2,
    "Bearer Token": 3.5,
    "API Token": 3.5,
    "API Key": 3.0,
}


# Obvious dummy/placeholder patterns to exclude
_DUMMY_PATTERNS: Set[str] = {
    "xxx",
    "XXX",
    "xxxx",
    "XXXX",
    "xxxxx",
    "XXXXX",
    "yyy",
    "YYY",
    "YYYY",
    "zzz",
    "ZZZ",
    "placeholder",
    "PLACEHOLDER",
    "Placeholder",
    "dummy",
    "DUMMY",
    "Dummy",
    "fake",
    "FAKE",
    "Fake",
    "your_token_here",
    "YOUR_TOKEN_HERE",
    "your_api_key",
    "YOUR_API_KEY",
    "insert_token",
    "INSERT_TOKEN",
    "changeme",
    "CHANGEME",
    "secret_here",
    "SECRET_HERE",
    "token_here",
    "TOKEN_HERE",
    "api_key_here",
    "API_KEY_HERE",
}

# Common words that indicate example/dummy values (e.g., sk-ml-team-abc123)
_DUMMY_WORDS: Set[str] = {"team", "test", "sample", "example", "demo", "dev"}


def _calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy in bits per character.

    High entropy (>3.5) = random-looking, likely real secret
    Low entropy (<2.5) = predictable, likely dummy value
    """
    if not text:
        return 0.0

    # Count character frequencies
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1

    # Calculate entropy
    length = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def _is_dummy_value(text: str) -> bool:
    """Check if text is an obvious dummy/placeholder value.

    Returns True for values like:
    - "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    - "sk-test-abc123xyz789"
    - "your_token_here"
    """
    text_lower = text.lower()

    # Check for obvious placeholder keywords
    for pattern in _DUMMY_PATTERNS:
        if pattern.lower() in text_lower:
            return True

    # Check for common dummy words (team, test, sample, etc.)
    # Use word boundaries to avoid false positives
    for word in _DUMMY_WORDS:
        if re.search(rf"\b{word}\b", text_lower):
            return True

    # Check for highly repetitive patterns (like all 'x' or 'X')
    if len(set(text)) <= 3 and len(text) > 10:
        return True

    # Check for sequential patterns at word boundaries only (abc123, xyz789 as whole words)
    # Avoid flagging real secrets containing these substrings
    if re.search(r"\b(abc|xyz|123|789|000|111)\b", text_lower):
        return True

    return False


def _get_entropy_threshold(token_type: str) -> float:
    """Get minimum entropy threshold for a token type."""
    return _ENTROPY_THRESHOLDS.get(token_type, _ENTROPY_THRESHOLDS["default"])


def _classify_token(pattern: str) -> str:
    """Return a human-readable token type label for a pattern."""
    for hint, label in _TOKEN_TYPE_HINTS:
        if hint in pattern:
            return label
    return "API Key"


def _extract_token_value(match: re.Match, line: str) -> str:
    """Extract the token value from a regex match."""
    # Try to get the first captured group, else the full match
    if match.groups():
        # Return the first non-None group
        for group in match.groups():
            if group is not None:
                return group
    return match.group(0)


def detect_tokens_in_content(
    content: str, patterns: List[str]
) -> List[Tuple[str, Optional[int]]]:
    """Detect tokens in file content using regex patterns with entropy filtering.

    Uses Shannon entropy to filter out dummy values like:
    - "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    - "sk-test-abc123xyz789"
    - "your_token_here"

    Real secrets have high entropy (>3.0-3.5 bits/char)
    Dummy values have low entropy (<2.5 bits/char) or obvious patterns

    Returns:
        List of (token_type, line_number) tuples
    """
    detected = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            try:
                # Check if pattern is marked as case-sensitive with 'CS:' prefix
                if pattern.startswith("CS:"):
                    actual_pattern = pattern[3:]
                    matches = list(re.finditer(actual_pattern, line))
                else:
                    matches = list(re.finditer(pattern, line, re.IGNORECASE))

                for match in matches:
                    token_value = _extract_token_value(match, line)
                    token_type = _classify_token(pattern)

                    # Skip obvious dummy values
                    if _is_dummy_value(token_value):
                        continue

                    # Check entropy - real secrets are random (high entropy)
                    entropy = _calculate_entropy(token_value)
                    threshold = _get_entropy_threshold(token_type)

                    if entropy >= threshold:
                        detected.append((token_type, line_num))
                        # Only report first match per line to avoid spam
                        break

            except re.error:
                continue

        # Only report first detection per line
        if detected and detected[-1][1] == line_num:
            break

    return detected


def get_default_token_patterns() -> List[str]:
    """Return default regex patterns for token detection."""
    return [
        r"ghp_[a-zA-Z0-9]{36}",
        r"gho_[a-zA-Z0-9]{36}",
        r"ghu_[a-zA-Z0-9]{36}",
        r"ghs_[a-zA-Z0-9]{36}",
        r"ghr_[a-zA-Z0-9]{36}",
        r"AKIA[0-9A-Z]{16}",
        r"sk-[a-zA-Z0-9]{48}",
        r"xoxb-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}",
        r"xoxp-[0-9]{13}-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}",
        r"glpat-[a-zA-Z0-9_-]{20}",
        r"pk_live_[a-zA-Z0-9]{24}",
        r"pk_test_[a-zA-Z0-9]{24}",
        r"sk_live_[a-zA-Z0-9]{24}",
        r"sk_test_[a-zA-Z0-9]{24}",
        r"sk-or-v1-(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9_-]{32,}",
        r"CS:^[A-Z][A-Z0-9_]*(?:API|KEY|TOKEN|SECRET|AUTH|PASS|PWD|CREDENTIAL|ACCESS)[A-Z0-9_]*=(?=(?:.*[a-z]))(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9_-]{20,}",
        r"\bBearer\s+(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[a-zA-Z0-9_-]{32,}\b",
        r"\bToken\s+(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[a-zA-Z0-9_-]{32,}\b",
        r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----",
        r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----",
        r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
        r"-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----",
    ]
