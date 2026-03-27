"""Utilities for handling co-authors in commit messages."""

import re
from typing import List, Dict, Optional, Tuple


def format_co_author_trailer(name: str, email: str) -> str:
    """Format a co-author trailer for git commit messages.
    
    Args:
        name: Author's name
        email: Author's email
        
    Returns:
        Formatted co-author trailer
    """
    return f"Co-authored-by: {name} <{email}>"


def parse_co_authors(message: str) -> List[Dict[str, str]]:
    """Parse co-author trailers from a commit message.
    
    Args:
        message: Commit message content
        
    Returns:
        List of co-author dictionaries with name and email
    """
    co_authors = []
    
    # Pattern to match "Co-authored-by: Name <email>"
    pattern = re.compile(r'^Co-authored-by:\s*(.+?)\s+<(.+?)>\s*$', re.MULTILINE | re.IGNORECASE)
    
    for match in pattern.finditer(message):
        name = match.group(1).strip()
        email = match.group(2).strip()
        co_authors.append({'name': name, 'email': email})
    
    return co_authors


def add_co_authors_to_message(message: str, co_authors: List[Dict[str, str]]) -> str:
    """Add co-author trailers to a commit message.
    
    Args:
        message: Original commit message
        co_authors: List of co-author dictionaries
        
    Returns:
        Message with co-author trailers added
    """
    if not co_authors:
        return message
    
    # Ensure message ends with newline
    if not message.endswith('\n'):
        message += '\n'
    
    # Add empty line if message doesn't end with one
    if not message.endswith('\n\n'):
        message += '\n'
    
    # Add co-author trailers
    for author in co_authors:
        trailer = format_co_author_trailer(author['name'], author['email'])
        message += f"{trailer}\n"
    
    return message


def remove_co_authors_from_message(message: str) -> Tuple[str, List[Dict[str, str]]]:
    """Remove co-author trailers from a commit message.
    
    Args:
        message: Commit message with co-author trailers
        
    Returns:
        Tuple of (cleaned_message, removed_co_authors)
    """
    co_authors = parse_co_authors(message)
    
    # Remove co-author lines
    lines = message.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if not re.match(r'^Co-authored-by:', line, re.IGNORECASE):
            cleaned_lines.append(line)
        else:
            # Stop removing once we hit the first co-author
            # and there are only co-authors remaining
            pass
    
    # Remove trailing empty lines
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    cleaned_message = '\n'.join(cleaned_lines)
    
    return cleaned_message, co_authors


def validate_author_format(author_str: str) -> Optional[Dict[str, str]]:
    """Validate and parse an author string.
    
    Accepts formats:
    - Name <email>
    - email@domain.com
    - alias (looked up from project authors)
    
    Args:
        author_str: Author string to validate
        
    Returns:
        Dictionary with name and email, or None if invalid
    """
    # Try "Name <email>" format
    match = re.match(r'^([^<]+?)\s+<(.+?)@(.+?)>$', author_str.strip())
    if match:
        name = match.group(1).strip()
        email = f"{match.group(2)}@{match.group(3)}"
        return {'name': name, 'email': email}
    
    # Try email format
    match = re.match(r'^(.+?)@(.+?)\.(.+?)$', author_str.strip())
    if match:
        return {'name': author_str, 'email': author_str}
    
    # Could be an alias - would need AuthorsManager to resolve
    return None


def deduplicate_co_authors(co_authors: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicate co-authors from list.
    
    Args:
        co_authors: List of co-author dictionaries
        
    Returns:
        Deduplicated list
    """
    seen = set()
    deduped = []
    
    for author in co_authors:
        email = author.get('email', '').lower()
        if email and email not in seen:
            seen.add(email)
            deduped.append(author)
    
    return deduped


def get_co_authors_from_command_line(co_author_args: List[str]) -> List[Dict[str, str]]:
    """Parse co-author arguments from command line.
    
    Args:
        co_author_args: List of author strings from --co-author flags
        
    Returns:
        List of co-author dictionaries
    """
    co_authors = []
    
    for arg in co_author_args:
        author = validate_author_format(arg)
        if author:
            co_authors.append(author)
        else:
            # Could be an alias - return as is for later resolution
            co_authors.append({'alias': arg, 'name': arg, 'email': arg})
    
    return deduplicate_co_authors(co_authors)


def format_commit_message_with_co_authors(title: str, body: Optional[str] = None,
                                         co_authors: Optional[List[Dict[str, str]]] = None) -> str:
    """Format a complete commit message with co-authors.
    
    Args:
        title: Commit message title
        body: Optional commit message body
        co_authors: Optional list of co-authors
        
    Returns:
        Formatted commit message
    """
    message = title
    
    if body:
        message += f'\n\n{body}'
    
    if co_authors:
        message = add_co_authors_to_message(message, co_authors)
    
    return message


def extract_current_author_from_config() -> Dict[str, str]:
    """Extract current author from user config.
    
    Returns:
        Dictionary with name and email
    """
    from goal.user_config import UserConfig
    
    user_config = UserConfig()
    
    return {
        'name': user_config.get('author_name', 'Unknown Author'),
        'email': user_config.get('author_email', 'unknown@example.com')
    }
