#!/bin/bash
# Demo script showing Goal markdown output usage

echo "=== Goal Markdown Output Demo ==="
echo

# Show current status in markdown
echo "1. Current status (markdown format):"
echo "-----------------------------------"
goal status --markdown
echo

# Dry run with markdown
echo "2. Dry run preview (markdown format):"
echo "--------------------------------------"
goal push --dry-run --markdown | head -50
echo "..."
echo

# Extract specific information using grep
echo "3. Extracting specific information:"
echo "-----------------------------------"
echo "Version bump will be:"
goal push --dry-run --markdown | grep "version_bump" | cut -d'"' -f2
echo

echo "Files that will be changed:"
goal push --dry-run --markdown | grep -A 20 "## Changed Files" | grep "^- " | wc -l
echo "files"
echo

# Save to file for later processing
echo "4. Saving output to file:"
echo "-------------------------"
goal push --dry-run --markdown > release-plan.md
echo "Saved to release-plan.md"
echo

# Show how to parse in Python
echo "5. Python parsing example:"
echo "-------------------------"
cat << 'EOF'
import subprocess
import yaml

# Get markdown output
result = subprocess.run(['goal', 'push', '--dry-run', '--markdown'], 
                       capture_output=True, text=True)

# Parse front matter
lines = result.stdout.split('\n')
if lines[0] == '---':
    front_matter = {}
    i = 1
    while lines[i] != '---':
        if ': ' in lines[i]:
            key, value = lines[i].split(': ', 1)
            try:
                front_matter[key] = yaml.safe_load(value)
            except:
                front_matter[key] = value.strip('"')
        i += 1
    
    print(f"Project: {front_matter.get('project_types')[0]}")
    print(f"Version: {front_matter.get('version_bump')}")
    print(f"Files: {front_matter.get('file_count')}")
EOF

echo
echo "=== Demo Complete ==="
