"""Git operations and interactive repository management."""

import subprocess
import os
import sys
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import click

# Try to import clickmd for enhanced formatting
try:
    from clickmd import echo_md
    HAS_CLICKMD = True
except ImportError:
    HAS_CLICKMD = False
    def echo_md(text, **kwargs):
        """Fallback when clickmd is not available."""
        click.echo(text)

__all__ = ['run_git', 'run_command', '_echo_cmd', '_run_git_verbose', 'run_git_with_status', 'HAS_CLICKMD', 'echo_md']

# =============================================================================
# Core Git Execution
# =============================================================================

def run_git(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    result = subprocess.run(
        ['git'] + list(args),
        capture_output=capture,
        text=True
    )
    return result


def run_command(command: str, capture: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        command,
        shell=True,
        capture_output=capture,
        text=True
    )


def _echo_cmd(args: List[str]) -> None:
    """Display a git command that is about to run, for transparency."""
    cmd_str = ' '.join(args)
    if HAS_CLICKMD:
        echo_md(f"```bash\n{' '.join(args)}\n```")
    else:
        click.echo(click.style(f"  → {cmd_str}", fg='bright_black'))


def _run_git_verbose(*args, capture=True) -> subprocess.CompletedProcess:
    """Run a git command, display it first, and return the result."""
    _echo_cmd(['git'] + list(args))
    
    # Show operation type with colors
    if args[0] in ['add', 'commit', 'push', 'pull', 'fetch']:
        operation = args[0].upper()
        if HAS_CLICKMD:
            echo_md(f"\n### 🔄 Git {operation}")
        else:
            click.echo(click.style(f"\n🔄 Git {operation}", fg='blue', bold=True))
    
    result = run_git(*args, capture=capture)
    
    # Show result summary for important operations
    if not capture and args[0] in ['push', 'pull', 'commit']:
        if result.returncode == 0:
            if HAS_CLICKMD:
                echo_md(f"✅ **Success**: {operation} completed")
            else:
                click.echo(click.style(f"✅ Success: {operation} completed", fg='green'))
        else:
            if HAS_CLICKMD:
                echo_md(f"❌ **Error**: {operation} failed")
            else:
                click.echo(click.style(f"❌ Error: {operation} failed", fg='red'))
    
    return result


def run_git_with_status(*args, capture=True, show_output=False) -> subprocess.CompletedProcess:
    """Run git command with enhanced status display."""
    # Show the command
    _echo_cmd(['git'] + list(args))
    
    # Run the command
    result = run_git(*args, capture=capture)
    
    # Show detailed status
    if show_output or result.returncode != 0:
        if HAS_CLICKMD:
            echo_md(f"\n**Output:**")
            echo_md("```")
            if result.stdout:
                click.echo(result.stdout)
            if result.stderr:
                click.echo(result.stderr, err=True)
            echo_md("```")
        else:
            if result.stdout:
                click.echo(click.style("Output:", fg='cyan'))
                click.echo(result.stdout)
            if result.stderr:
                click.echo(click.style("Error:", fg='red'))
                click.echo(result.stderr, err=True)
    
    # Show exit status
    if result.returncode == 0:
        if HAS_CLICKMD:
            echo_md(f"✅ **Exit code**: {result.returncode}")
        else:
            click.echo(click.style(f"✅ Exit code: {result.returncode}", fg='green'))
    else:
        if HAS_CLICKMD:
            echo_md(f"❌ **Exit code**: {result.returncode}")
        else:
            click.echo(click.style(f"❌ Exit code: {result.returncode}", fg='red'))
    
    return result


def run_command_tee(command: str) -> subprocess.CompletedProcess:
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output: List[str] = []
    if proc.stdout is not None:
        for chunk in proc.stdout:
            output.append(chunk)
            click.echo(chunk, nl=False)
            sys.stdout.flush()

    returncode = proc.wait()
    return subprocess.CompletedProcess(args=command, returncode=returncode, stdout=''.join(output), stderr='')


# =============================================================================
# Repository Checks & Validation
# =============================================================================

def is_git_repository() -> bool:
    """Check if the current directory is inside a git repository."""
    if Path('.git').exists():
        return True
    result = run_git('rev-parse', '--git-dir')
    return result.returncode == 0


def validate_repo_url(url: str) -> bool:
    """Validate that a URL looks like a git repository (HTTP/HTTPS/SSH/file)."""
    url = url.strip()
    # SSH format: git@host:user/repo.git
    if re.match(r'^git@[\w.\-]+:[\w.\-/]+(?:\.git)?$', url):
        return True
    # HTTP(S) format
    if re.match(r'^https?://[\w.\-]+/[\w.\-/]+(?:\.git)?$', url):
        return True
    # File protocol format
    if re.match(r'^file://.*$', url):
        return True
    return False


# =============================================================================
# Remote Management
# =============================================================================

def get_remote_url(remote: str = 'origin') -> Optional[str]:
    """Get the URL of a named remote, or None."""
    result = run_git('remote', 'get-url', remote)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def list_remotes() -> List[Tuple[str, str]]:
    """Return list of (name, url) for all configured remotes."""
    result = run_git('remote', '-v')
    if result.returncode != 0 or not result.stdout.strip():
        return []
    seen = {}
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] not in seen:
            seen[parts[0]] = parts[1]
    return list(seen.items())


def _prompt_remote_url() -> Optional[str]:
    """Ask the user for a remote URL with examples. Returns URL or None."""
    click.echo()
    click.echo(click.style("Enter repository URL:", fg='cyan'))
    click.echo(click.style("  SSH   example: git@github.com:user/repo.git", fg='bright_black'))
    click.echo(click.style("  HTTP  example: https://github.com/user/repo.git", fg='bright_black'))
    url = click.prompt("URL", default='', show_default=False).strip()
    if not url:
        return None
    if not validate_repo_url(url):
        click.echo(click.style("✗ Invalid repository URL format.", fg='red'))
        return None
    return url


def _list_remote_branches(remote: str = 'origin') -> List[str]:
    """Fetch and list branches on a remote."""
    _echo_cmd(['git', 'ls-remote', '--heads', remote])
    result = run_git('ls-remote', '--heads', remote)
    if result.returncode != 0 or not result.stdout.strip():
        return []
    branches = []
    for line in result.stdout.strip().splitlines():
        parts = line.split('\t')
        if len(parts) == 2:
            ref = parts[1]
            branch = ref.replace('refs/heads/', '')
            branches.append(branch)
    return branches


def get_remote_branch() -> str:
    """Get the current branch name."""
    result = run_git('rev-parse', '--abbrev-ref', 'HEAD')
    return result.stdout.strip() if result.returncode == 0 else 'main'


# =============================================================================
# Interactive Setup Flow
# =============================================================================

def clone_repository(url: str, target_dir: Optional[str] = None) -> Tuple[bool, str]:
    """Clone a git repository from a URL.

    Args:
        url: Repository URL (HTTP/HTTPS/SSH).
        target_dir: Optional target directory name. If None, git decides.

    Returns:
        Tuple of (success, message).
    """
    url = url.strip()
    if not validate_repo_url(url):
        return False, f"Invalid repository URL: {url}\nExpected format: https://... or git@host:user/repo.git"

    args = ['clone', url]
    if target_dir:
        args.append(target_dir)

    click.echo(click.style(f"Cloning {url} ...", fg='cyan'))
    result = run_git(*args, capture=False)
    if result.returncode == 0:
        # Determine the directory name that was created
        if target_dir:
            repo_dir = target_dir
        else:
            # Extract repo name from URL
            repo_name = url.rstrip('/').rsplit('/', 1)[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            repo_dir = repo_name
        return True, repo_dir
    else:
        return False, "Failed to clone repository. Check the URL and your access permissions."


def _select_branch(branches: list) -> str:
    """Prompt user to select a branch from a list, or auto-select if only one."""
    if len(branches) == 1:
        click.echo(click.style(f"  Using branch: {branches[0]}", fg='bright_black'))
        return branches[0]
    branch_list = '\n'.join(f"  [{i+1}] {b}" for i, b in enumerate(branches))
    idx = click.prompt(
        f"{click.style('Select branch:', fg='cyan')}\n{branch_list}\nChoose",
        type=click.IntRange(1, len(branches)),
        default=1,
    )
    return branches[idx - 1]


def _handle_merge_strategy(branches: list, has_files: bool) -> None:
    """Prompt for and execute a merge strategy after fetching remote branches."""
    if not branches:
        click.echo(click.style("  Remote is empty (no branches yet). Your local files will be the first push.", fg='bright_black'))
        return

    click.echo(click.style(f"  Remote branches: {', '.join(branches)}", fg='bright_black'))
    click.echo()

    merge_action = click.prompt(
        f"{click.style('How should goal combine local and remote files?', fg='cyan')}\n"
        f"  [1] Keep local files, push to remote later     (recommended for new projects)\n"
        f"  [2] Merge remote branch into local files       (combine both)\n"
        f"  [3] Reset local to remote branch               (overwrite local with remote)\n"
        f"  [4] Skip — just keep the remote configured\n"
        f"Choose",
        type=click.IntRange(1, 4),
        default=1,
    )

    if merge_action not in (2, 3):
        return

    branch = _select_branch(branches)

    if merge_action == 2:
        if has_files:
            _run_git_verbose('add', '-A')
            _run_git_verbose('commit', '-m', 'chore: initial local state before merge')
        result = _run_git_verbose('merge', f'origin/{branch}', '--allow-unrelated-histories', '--no-edit')
        if result.returncode != 0:
            click.echo(click.style(
                f"⚠  Merge conflict detected. Resolve manually, then run goal again.",
                fg='yellow', bold=True
            ))
            click.echo(click.style(f"  Hint: git status  →  resolve  →  git add .  →  git merge --continue", fg='bright_black'))
        else:
            click.echo(click.style(f"✓ Merged origin/{branch} into local files.", fg='green'))
    elif merge_action == 3:
        result = _run_git_verbose('checkout', f'origin/{branch}', '-B', branch)
        if result.returncode == 0:
            click.echo(click.style(f"✓ Local files replaced with origin/{branch}.", fg='green'))
        else:
            click.echo(click.style(f"✗ Failed to checkout: {result.stderr.strip()}", fg='red'))


def _handle_init_remote(has_files: bool) -> bool:
    """git init + add remote + optional fetch/merge."""
    result = _run_git_verbose('init')
    if result.returncode != 0:
        click.echo(click.style("✗ Failed to initialize git repository.", fg='red'))
        return False
    click.echo(click.style("✓ Initialized git repository.", fg='green'))

    url = _prompt_remote_url()
    if url:
        result = _run_git_verbose('remote', 'add', 'origin', url)
        if result.returncode != 0:
            click.echo(click.style(f"✗ Could not add remote: {result.stderr.strip()}", fg='red'))
        else:
            click.echo(click.style(f"✓ Remote 'origin' → {url}", fg='green'))

        click.echo()
        click.echo(click.style("Fetching remote branches...", fg='cyan'))
        fetch_result = _run_git_verbose('fetch', 'origin')
        if fetch_result.returncode == 0:
            _handle_merge_strategy(_list_remote_branches('origin'), has_files)
        else:
            click.echo(click.style(f"⚠  Could not fetch remote: {fetch_result.stderr.strip()}", fg='yellow'))
            click.echo(click.style("  Remote is configured but unreachable. Check URL and credentials.", fg='bright_black'))

    click.echo(click.style(f"\n✓ Ready. Run 'goal' again to commit and push.", fg='green', bold=True))
    return True


def _handle_clone() -> bool:
    """Clone a remote repository into the current directory."""
    url = _prompt_remote_url()
    if not url:
        return False
    success, msg = clone_repository(url)
    if success:
        os.chdir(msg)
        click.echo(click.style(f"✓ Cloned and entered '{msg}'", fg='green', bold=True))
        return True
    click.echo(click.style(f"✗ {msg}", fg='red'))
    return False


def _handle_local_init() -> bool:
    """Initialize a local-only git repository."""
    result = _run_git_verbose('init')
    if result.returncode == 0:
        click.echo(click.style("✓ Initialized local git repository (no remote).", fg='green', bold=True))
        return True
    click.echo(click.style("✗ Failed to initialize git repository.", fg='red'))
    return False


def ensure_git_repository(auto: bool = False) -> bool:
    """Check for a git repo; if missing, interactively offer options.

    When *auto* is True (``goal -a``), skip interactive prompts and return
    False so the caller can abort gracefully.

    Returns True if we end up inside a valid git repository, False otherwise.
    """
    if is_git_repository():
        return True

    click.echo(click.style("⚠  Not a git repository.", fg='yellow', bold=True))

    if auto:
        click.echo(click.style("  Skipping (--all mode, no interactive prompts).", fg='yellow'))
        return False

    click.echo()
    has_files = any(Path('.').iterdir())
    cwd_name = Path('.').resolve().name

    action = click.prompt(
        f"{click.style('What would you like to do?', fg='cyan')}\n"
        f"  [1] Initialize git here and connect to a remote  (keeps local files in '{cwd_name}/')\n"
        f"  [2] Clone a remote repository into this directory  (downloads remote files)\n"
        f"  [3] Initialize a local-only git repository        (no remote)\n"
        f"  [4] Exit\n"
        f"Choose",
        type=click.IntRange(1, 4),
        default=1,
    )

    handlers = {
        1: lambda: _handle_init_remote(has_files),
        2: _handle_clone,
        3: _handle_local_init,
    }
    return handlers.get(action, lambda: False)()


def ensure_remote(auto: bool = False) -> bool:
    """Ensure a git remote is configured. Offers interactive setup if missing.

    When *auto* is True, silently returns False if no remote is found.
    Returns True if a remote is available, False otherwise.
    """
    remotes = list_remotes()
    if remotes:
        return True

    click.echo(click.style("⚠  No git remote configured.", fg='yellow', bold=True))

    if auto:
        click.echo(click.style("  Skipping remote setup (--all mode). Commit will be local only.", fg='yellow'))
        return False

    click.echo()
    action = click.prompt(
        f"{click.style('Would you like to add a remote?', fg='cyan')}\n"
        f"  [1] Add remote origin (connect to GitHub/GitLab/etc.)\n"
        f"  [2] Skip — commit locally without pushing\n"
        f"Choose",
        type=click.IntRange(1, 2),
        default=1,
    )

    if action == 1:
        url = _prompt_remote_url()
        if not url:
            return False
        result = _run_git_verbose('remote', 'add', 'origin', url)
        if result.returncode != 0:
            click.echo(click.style(f"✗ Could not add remote: {result.stderr.strip()}", fg='red'))
            return False
        click.echo(click.style(f"✓ Remote 'origin' → {url}", fg='green', bold=True))

        # Verify connectivity
        click.echo(click.style("  Verifying connection...", fg='bright_black'))
        verify = run_git('ls-remote', '--exit-code', 'origin')
        if verify.returncode == 0:
            click.echo(click.style("  ✓ Remote is reachable.", fg='green'))
        else:
            click.echo(click.style("  ⚠  Remote is not reachable (check URL/credentials). Push may fail.", fg='yellow'))
        return True

    return False


# =============================================================================
# Git Diff Analysis
# =============================================================================

def get_staged_files() -> List[str]:
    """Get list of staged files."""
    result = run_git('diff', '--cached', '--name-only')
    return result.stdout.strip().splitlines() if result.stdout.strip() else []


def get_unstaged_files() -> List[str]:
    """Get list of unstaged/untracked files."""
    result = run_git('status', '--porcelain')
    return [line[3:] for line in result.stdout.strip().splitlines() if line]


def get_working_tree_files() -> List[str]:
    """Get list of files changed in working tree (unstaged + untracked)."""
    changed = run_git('diff', '--name-only').stdout.strip().splitlines()
    untracked = run_git('ls-files', '--others', '--exclude-standard').stdout.strip().splitlines()

    files: List[str] = []
    for f in [*changed, *untracked]:
        f = (f or '').strip()
        if not f:
            continue
        if f not in files:
            files.append(f)
    return files


def get_diff_stats(cached: bool = True) -> Dict[str, Tuple[int, int]]:
    """Get additions/deletions per file."""
    result = run_git('diff', '--cached', '--numstat') if cached else run_git('diff', '--numstat')
    stats = {}
    for line in result.stdout.strip().splitlines():
        if line:
            parts = line.split('\t')
            if len(parts) == 3:
                adds = int(parts[0]) if parts[0] != '-' else 0
                dels = int(parts[1]) if parts[1] != '-' else 0
                stats[parts[2]] = (adds, dels)
    return stats


def get_diff_content(cached: bool = True, max_lines: int = 10000) -> str:
    """Get the actual diff content for analysis.
    
    For performance, if total changes exceed max_lines, returns a limited diff
    with summary stats instead of full content.
    """
    # First check stats to avoid loading huge diffs
    stats = get_diff_stats(cached)
    total_changes = sum(adds + dels for adds, dels in stats.values())
    
    if total_changes > max_lines:
        # For very large changes, return limited diff with just file names and stats
        result = run_git('diff', '--cached', '--stat') if cached else run_git('diff', '--stat')
        return f"# Large diff ({total_changes} lines changed)\n{result.stdout}"
    
    result = run_git('diff', '--cached', '-U3') if cached else run_git('diff', '-U3')
    return result.stdout


def read_ticket(path: Path = Path('TICKET')) -> Dict[str, str]:
    """Read TICKET configuration file (key=value)."""
    cfg: Dict[str, str] = {'prefix': '', 'format': '[{ticket}] {title}'}
    if not path.exists():
        return cfg
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            cfg[k.strip()] = v.strip()
    except Exception:
        return cfg
    return cfg


# Backward-compatible alias for the old typo name
read_tickert = read_ticket


def apply_ticket_prefix(title: str, ticket: Optional[str]) -> str:
    """Apply ticket prefix (from CLI or TICKET file) to commit title."""
    cfg = read_ticket()
    ticket_value = (ticket or cfg.get('prefix') or '').strip()
    if not ticket_value:
        return title
    fmt = cfg.get('format') or '[{ticket}] {title}'
    try:
        return fmt.format(ticket=ticket_value, title=title)
    except Exception:
        return f"[{ticket_value}] {title}"
