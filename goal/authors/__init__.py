"""Multi-author support for Goal projects.

Provides functionality for:
- Team-based author management
- Co-authored-by commit trailers
- Author attribution in commits
"""

from .manager import AuthorsManager, get_project_authors, add_project_author
from .utils import format_co_author_trailer, parse_co_authors, add_co_authors_to_message

__all__ = [
    "AuthorsManager",
    "get_project_authors",
    "add_project_author",
    "format_co_author_trailer",
    "parse_co_authors",
    "add_co_authors_to_message",
]
