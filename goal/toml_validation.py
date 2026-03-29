"""TOML validation utilities for early error detection."""

from pathlib import Path
from typing import Optional, Tuple


def get_tomllib():
    """Get the best available TOML library."""
    try:
        import tomllib
        return tomllib
    except ModuleNotFoundError:
        try:
            import tomli as tomllib
            return tomllib
        except ImportError:
            return None


def validate_toml_file(filepath: Path) -> Tuple[bool, Optional[str]]:
    """Validate a TOML file and return helpful error message if invalid.
    
    Args:
        filepath: Path to the TOML file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if TOML is valid, False otherwise
        - error_message: None if valid, helpful error message if invalid
    """
    if not filepath.exists():
        return True, None  # File doesn't exist, not an error
    
    tomllib = get_tomllib()
    if tomllib is None:
        return True, None  # Can't validate without tomllib
    
    content = filepath.read_text(encoding='utf-8')
    
    try:
        if hasattr(tomllib, 'loads'):
            tomllib.loads(content)
        return True, None
    except Exception as e:
        error_str = str(e)
        
        # Extract line number if available
        line_num = None
        if 'line' in error_str.lower():
            import re
            match = re.search(r'line\s+(\d+)', error_str, re.IGNORECASE)
            if match:
                line_num = int(match.group(1))
        
        # Build helpful error message
        msg_parts = [f"❌ TOML syntax error in {filepath}"]
        
        if line_num:
            msg_parts.append(f"   Line {line_num}: {error_str}")
            # Show the problematic line
            lines = content.split('\n')
            if 1 <= line_num <= len(lines):
                msg_parts.append(f"   Content: {lines[line_num - 1].strip()}")
        else:
            msg_parts.append(f"   {error_str}")
        
        msg_parts.append("\n💡 Fix the TOML syntax error before continuing.")
        msg_parts.append("   Common issues: trailing commas, missing quotes, invalid indentation")
        
        return False, '\n'.join(msg_parts)


def validate_project_toml_files(project_dir: Path = Path('.')) -> Tuple[bool, list]:
    """Validate all common TOML files in a project.
    
    Args:
        project_dir: Project directory to check
        
    Returns:
        Tuple of (all_valid, list_of_error_messages)
    """
    toml_files = [
        project_dir / 'pyproject.toml',
        project_dir / 'Cargo.toml',
        project_dir / 'Pipfile',
    ]
    
    errors = []
    all_valid = True
    
    for toml_file in toml_files:
        if toml_file.exists():
            is_valid, error = validate_toml_file(toml_file)
            if not is_valid:
                all_valid = False
                errors.append(error)
    
    return all_valid, errors


def check_pyproject_toml() -> Optional[str]:
    """Quick check for pyproject.toml validity.
    
    Returns:
        Error message if invalid, None if valid or file doesn't exist
    """
    pyproject = Path('pyproject.toml')
    if not pyproject.exists():
        return None
    
    is_valid, error = validate_toml_file(pyproject)
    return error if not is_valid else None
