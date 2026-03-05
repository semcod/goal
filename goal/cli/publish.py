"""Publishing functions - extracted from cli.py."""

import subprocess
import shutil
from pathlib import Path
from typing import List

try:
    from ..git_ops import run_command_tee
    from .version import PROJECT_TYPES
except ImportError:
    from goal.git_ops import run_command_tee
    from goal.cli.version import PROJECT_TYPES


def makefile_has_target(target: str) -> bool:
    """Check if Makefile has a specific target."""
    makefile = Path('Makefile')
    if not makefile.exists() or not makefile.is_file():
        return False
    try:
        content = makefile.read_text(errors='ignore')
    except Exception:
        return False
    import re
    return re.search(rf'^\s*{re.escape(target)}\s*:', content, re.MULTILINE) is not None


def publish_project(project_types: List[str], version: str, yes: bool = False) -> bool:
    """Publish project to appropriate package registries."""
    success = True
    
    for ptype in project_types:
        config = PROJECT_TYPES.get(ptype, {})
        publish_cmd = config.get('publish_command', '')
        
        if not publish_cmd:
            continue
        
        # Skip if dry-run would be triggered
        if '{version}' in publish_cmd:
            publish_cmd = publish_cmd.replace('{version}', version)
        
        try:
            result = subprocess.run(
                publish_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            if result.returncode != 0:
                import click
                click.echo(click.style(f"  Publish error: {result.stderr}", fg='red'), err=True)
                success = False
        except Exception:
            success = False
    
    return success


__all__ = [
    'makefile_has_target',
    'publish_project',
]
