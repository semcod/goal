"""Test bootstrap helpers."""

from pathlib import Path
import sys


# Ensure local package imports resolve in bare pytest runs.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
