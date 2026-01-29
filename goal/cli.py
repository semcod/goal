#!/usr/bin/env python3
"""Goal CLI - Automated git push with smart commit messages."""

import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

import click


def run_git(*args, capture=True):
    """Run a git command and return the result."""
    result = subprocess.run(
        ['git'] + list(args),
        capture_output=capture,
        text=True
    )
    return result


def get_staged_files():
    """Get list of staged files."""
    result = run_git('diff', '--cached', '--name-only')
    return result.stdout.strip().split('\n') if result.stdout.strip() else []


def get_unstaged_files():
    """Get list of unstaged/untracked files."""
    result = run_git('status', '--porcelain')
    return [line[3:] for line in result.stdout.strip().split('\n') if line]


def categorize_file(filename):
    """Categorize file and return appropriate description."""
    basename = os.path.basename(filename)
    
    # Special files
    if basename == 'Makefile':
        return "build: update Makefile"
    elif basename == 'package.json':
        return "deps: update package.json"
    elif basename in ('Dockerfile', 'docker-compose.yml'):
        return "docker: update " + basename
    elif basename in ('CHANGELOG.md', 'VERSION'):
        return None  # Skip these, they're auto-generated
    elif basename == 'README.md':
        return "docs: update README"
    elif filename.endswith('.md'):
        return f"docs: update {basename}"
    elif filename.endswith('.py'):
        return f"update {filename}"
    elif filename.endswith(('.js', '.ts', '.tsx', '.jsx')):
        return f"update {filename}"
    elif filename.endswith(('.yml', '.yaml')):
        return f"config: update {basename}"
    elif filename.endswith('.sh'):
        return f"scripts: update {basename}"
    else:
        return f"update {filename}"


def generate_commit_message(files):
    """Generate commit message based on changed files."""
    changes = []
    for f in files:
        if f:
            desc = categorize_file(f)
            if desc:
                changes.append(desc)
    
    if not changes:
        return None
    
    if len(changes) == 1:
        return changes[0]
    elif len(changes) <= 3:
        return "chore: " + ", ".join(changes)
    else:
        return f"chore: update {len(changes)} files"


def get_current_version():
    """Get current version from VERSION file or default to 1.0.0."""
    version_file = Path('VERSION')
    if version_file.exists():
        return version_file.read_text().strip()
    return "1.0.0"


def bump_version(version, bump_type='patch'):
    """Bump version based on type (major, minor, patch)."""
    parts = version.split('.')
    if len(parts) != 3:
        return "1.0.0"
    
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"


def update_version_file(new_version):
    """Update VERSION file."""
    Path('VERSION').write_text(new_version + '\n')


def update_changelog(version, files):
    """Update CHANGELOG.md with new version and changes."""
    changes = []
    for f in files:
        if f:
            desc = categorize_file(f)
            if desc:
                changes.append(desc)
    
    changelog_path = Path('CHANGELOG.md')
    existing_content = ""
    if changelog_path.exists():
        existing_content = changelog_path.read_text()
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    new_entry = f"## [{version}] - {date_str}\n\n"
    for change in changes:
        new_entry += f"- {change}\n"
    new_entry += "\n"
    
    changelog_path.write_text(new_entry + existing_content)


def get_remote_branch():
    """Get the current branch name."""
    result = run_git('rev-parse', '--abbrev-ref', 'HEAD')
    return result.stdout.strip() if result.returncode == 0 else 'main'


@click.group()
@click.version_option()
def main():
    """Goal - Automated git push with smart commit messages."""
    pass


@main.command()
@click.option('--bump', '-b', type=click.Choice(['patch', 'minor', 'major']), default='patch',
              help='Version bump type (default: patch)')
@click.option('--no-tag', is_flag=True, help='Skip creating git tag')
@click.option('--no-changelog', is_flag=True, help='Skip updating changelog')
@click.option('--message', '-m', help='Custom commit message (overrides auto-generation)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
def push(bump, no_tag, no_changelog, message, dry_run):
    """Add, commit, tag, and push changes to remote."""
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        result = run_git('rev-parse', '--git-dir')
        if result.returncode != 0:
            click.echo(click.style("Error: Not a git repository", fg='red'))
            sys.exit(1)
    
    # Stage all changes
    if not dry_run:
        run_git('add', '-A')
    
    # Get staged files
    files = get_staged_files()
    if not files or files == ['']:
        click.echo(click.style("No changes to commit.", fg='yellow'))
        return
    
    # Generate or use provided commit message
    if message:
        commit_msg = message
    else:
        commit_msg = generate_commit_message(files)
        if not commit_msg:
            click.echo(click.style("No changes to commit.", fg='yellow'))
            return
    
    # Get version info
    current_version = get_current_version()
    new_version = bump_version(current_version, bump)
    
    if dry_run:
        click.echo(click.style("=== DRY RUN ===", fg='cyan', bold=True))
        click.echo(f"Files to commit: {len(files)}")
        for f in files[:10]:
            click.echo(f"  - {f}")
        if len(files) > 10:
            click.echo(f"  ... and {len(files) - 10} more")
        click.echo(f"Commit message: {commit_msg}")
        click.echo(f"Version: {current_version} -> {new_version}")
        if not no_tag:
            click.echo(f"Tag: v{new_version}")
        return
    
    # Update changelog
    if not no_changelog:
        update_changelog(new_version, files)
        run_git('add', 'CHANGELOG.md')
        click.echo(click.style(f"✓ Updated CHANGELOG.md", fg='green'))
    
    # Update version file
    update_version_file(new_version)
    run_git('add', 'VERSION')
    click.echo(click.style(f"✓ Updated VERSION to {new_version}", fg='green'))
    
    # Commit
    result = run_git('commit', '-m', commit_msg)
    if result.returncode != 0:
        click.echo(click.style(f"Error committing: {result.stderr}", fg='red'))
        sys.exit(1)
    click.echo(click.style(f"✓ Committed: {commit_msg}", fg='green'))
    
    # Create tag
    if not no_tag:
        tag_name = f"v{new_version}"
        result = run_git('tag', '-a', tag_name, '-m', f"Release {new_version}")
        if result.returncode != 0:
            click.echo(click.style(f"Warning: Could not create tag: {result.stderr}", fg='yellow'))
        else:
            click.echo(click.style(f"✓ Created tag: {tag_name}", fg='green'))
    
    # Push
    branch = get_remote_branch()
    if no_tag:
        result = run_git('push', 'origin', branch, capture=False)
    else:
        result = run_git('push', 'origin', branch, '--tags', capture=False)
    
    if result.returncode != 0:
        click.echo(click.style("Error pushing to remote", fg='red'))
        sys.exit(1)
    
    click.echo(click.style(f"\n✓ Successfully pushed to {branch}", fg='green', bold=True))


@main.command()
def status():
    """Show current git status and version info."""
    # Version
    version = get_current_version()
    click.echo(f"Version: {click.style(version, fg='cyan')}")
    
    # Branch
    branch = get_remote_branch()
    click.echo(f"Branch: {click.style(branch, fg='cyan')}")
    
    # Staged files
    staged = get_staged_files()
    if staged and staged != ['']:
        click.echo(f"\nStaged files ({len(staged)}):")
        for f in staged:
            click.echo(f"  {click.style('+', fg='green')} {f}")
    
    # Unstaged files
    unstaged = get_unstaged_files()
    if unstaged:
        click.echo(f"\nUnstaged/untracked ({len(unstaged)}):")
        for f in unstaged[:10]:
            click.echo(f"  {click.style('?', fg='yellow')} {f}")
        if len(unstaged) > 10:
            click.echo(f"  ... and {len(unstaged) - 10} more")


@main.command()
@click.option('--type', '-t', 'bump_type', type=click.Choice(['patch', 'minor', 'major']), default='patch',
              help='Version bump type')
def version(bump_type):
    """Show or bump version."""
    current = get_current_version()
    new = bump_version(current, bump_type)
    click.echo(f"Current: {current}")
    click.echo(f"Next ({bump_type}): {new}")


@main.command()
def init():
    """Initialize goal in current repository (creates VERSION and CHANGELOG.md if missing)."""
    version_file = Path('VERSION')
    changelog_file = Path('CHANGELOG.md')
    
    if not version_file.exists():
        version_file.write_text("1.0.0\n")
        click.echo(click.style("✓ Created VERSION file (1.0.0)", fg='green'))
    else:
        click.echo(f"VERSION exists: {version_file.read_text().strip()}")
    
    if not changelog_file.exists():
        changelog_file.write_text("""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
""")
        click.echo(click.style("✓ Created CHANGELOG.md", fg='green'))
    else:
        click.echo("CHANGELOG.md exists")
    
    click.echo(click.style("\n✓ Goal initialized!", fg='green', bold=True))


if __name__ == '__main__':
    main()
