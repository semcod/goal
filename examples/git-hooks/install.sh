#!/bin/bash
# Install Goal's git hooks

set -e

HOOK_DIR="$(git rev-parse --git-dir)/hooks"
SCRIPT_DIR="$(dirname "$0")"

echo "Installing Goal git hooks..."

# Create hooks directory if it doesn't exist
mkdir -p "$HOOK_DIR"

# Install prepare-commit-msg hook
if [ -f "$SCRIPT_DIR/prepare-commit-msg" ]; then
    cp "$SCRIPT_DIR/prepare-commit-msg" "$HOOK_DIR/"
    chmod +x "$HOOK_DIR/prepare-commit-msg"
    echo "✓ Installed prepare-commit-msg hook"
else
    echo "✗ prepare-commit-msg not found"
    exit 1
fi

echo ""
echo "Git hooks installed successfully!"
echo ""
echo "The prepare-commit-msg hook will automatically generate"
echo "smart commit messages when you run 'git commit' without a message."
echo ""
echo "To uninstall, remove the hook file:"
echo "  rm $HOOK_DIR/prepare-commit-msg"
