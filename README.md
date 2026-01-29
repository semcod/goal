# Goal

Automated git push with smart commit messages, changelog updates, and version tagging.

## Installation

```bash
pip install goal-push
```

## Usage

### Initialize a repository

```bash
goal init
```

Creates `VERSION` and `CHANGELOG.md` files if they don't exist.

### Push changes

```bash
goal push
```

This will:
1. Stage all changes (`git add -A`)
2. Generate a smart commit message based on changed files
3. Update `CHANGELOG.md` with the changes
4. Bump the version in `VERSION` file
5. Create a git tag
6. Push to remote with tags

### Options

```bash
goal push --bump minor    # Bump minor version instead of patch
goal push --bump major    # Bump major version
goal push --no-tag        # Skip creating git tag
goal push --no-changelog  # Skip updating changelog
goal push -m "message"    # Use custom commit message
goal push --dry-run       # Show what would happen without doing it
```

### Other commands

```bash
goal status   # Show current git status and version info
goal version  # Show current and next version
```

## Makefile integration

Replace your manual push target with:

```makefile
push:
	goal push
```

## License

MIT