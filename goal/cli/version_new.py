"""Version management functions - extracted from cli.py."""

import re
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple

try:
    from ..git_ops import run_git
    from ..version_validation import update_badge_versions
except ImportError:
    from goal.git_ops import run_git
    from goal.version_validation import update_badge_versions


# Project type definitions with version patterns
PROJECT_TYPES = {
    'python': {
        'files': ['pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt', 'Pipfile', 'environment.yml', 'poetry.lock', 'uv.lock', 'Pipfile.lock'],
        'version_patterns': {
            'pyproject.toml': r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'setup.py': r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            'setup.cfg': r'^version\s*=\s*(\d+\.\d+\.\d+)',
        },
        'test_command': 'python -m pytest',
        'publish_command': 'python -m build && python -m twine upload --skip-existing dist/*',
    },
    'nodejs': {
        'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb'],
        'version_patterns': {
