# User Configuration

Goal provides automatic project metadata management using your git configuration and license preferences. This guide explains how the user configuration system works and how to manage it.

## Overview

The user configuration system:
- **Stores** your preferences in `~/.goal`
- **Auto-detects** git user information
- **Remembers** your license choice
- **Updates** project files automatically
- **Preserves** existing authors

## First-Time Setup

### Automatic Detection

When you run Goal for the first time, it will:

1. **Detect your git configuration**:
   - Reads `git config user.name`
   - Reads `git config user.email`

2. **Ask for license preference** (one-time):
   ```
   ======================================================================
     📄 License Selection
   ======================================================================
   
   Please select your preferred default license:
   
     1. Apache License 2.0
     2. MIT License
     3. GNU General Public License v3.0
     4. BSD 3-Clause License
     5. GNU General Public License v2.0
     6. GNU Lesser General Public License v3.0
     7. GNU Affero General Public License v3.0
     8. Mozilla Public License 2.0
   
   Enter your choice [1]:
   ```

3. **Save to ~/.goal**:
   ```json
   {
     "author_name": "Tom Sapletta",
     "author_email": "info@softreck.com",
     "license": "Apache-2.0",
     "license_name": "Apache License 2.0",
     "license_classifier": "License :: OSI Approved :: Apache Software License"
   }
   ```

### Manual Configuration

If git is not configured, Goal will prompt you:

```bash
⚠ Git user information not configured!

Please configure git first:
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"

Enter your name: Tom Sapletta
Enter your email: info@softreck.com
```

## What Gets Updated

Every time you run `goal`, it automatically updates:

### Project Files

#### pyproject.toml (Python)
```toml
# Before
authors = [
    {name = "Original Author", email = "original@example.com"}
]
license = "MIT"

# After - Goal ADDS you, doesn't replace
authors = [
    {name = "Original Author", email = "original@example.com"},
    {name = "Tom Sapletta", email = "info@softreck.com"},
]
license = {text = "Apache-2.0"}

classifiers = [
    "License :: OSI Approved :: Apache Software License",
]
```

#### package.json (Node.js)
```json
{
  "author": "Original Author <original@example.com>",
  "contributors": [
    "Tom Sapletta <info@softreck.com>"
  ],
  "license": "Apache-2.0"
}
```

#### Cargo.toml (Rust)
```toml
authors = ["Original <old@email.com>", "Tom Sapletta <info@softreck.com>"]
license = "Apache-2.0"
```

### README.md

#### License Badges

Goal updates license badges automatically:

```markdown
<!-- Apache-2.0 -->
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

<!-- MIT -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- GPL-3.0 -->
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
```

#### License Section

Creates or updates:
```markdown
## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
```

#### Author Section

Creates or updates:
```markdown
## Author

Created by **Tom Sapletta** - [info@softreck.com](mailto:info@softreck.com)
```

## Smart Author Management

Goal intelligently manages authors:

### Scenario 1: No Existing Author
```python
# Before: Empty or no authors field
authors = []

# After: Goal adds you
authors = [
    {name = "Tom Sapletta", email = "info@softreck.com"}
]
```

### Scenario 2: Different Existing Author
```python
# Before: Someone else is the author
authors = [
    {name = "Alice Developer", email = "alice@example.com"}
]

# After: Goal adds you as co-author
authors = [
    {name = "Alice Developer", email = "alice@example.com"},
    {name = "Tom Sapletta", email = "info@softreck.com"},
]
```

### Scenario 3: You're Already an Author
```python
# Before: You're already listed
authors = [
    {name = "Tom Sapletta", email = "info@softreck.com"}
]

# After: No change (Goal checks by email)
authors = [
    {name = "Tom Sapletta", email = "info@softreck.com"}
]
```

## Managing Configuration

### View Current Configuration

```bash
$ goal config

======================================================================
  📋 Goal User Configuration
======================================================================

Config file: /home/tom/.goal

Current settings:
  Author name:  Tom Sapletta
  Author email: info@softreck.com
  License:      Apache License 2.0 (Apache-2.0)

💡 Tip: Run 'goal config --reset' to reconfigure
```

### Reset Configuration

```bash
$ goal config --reset

# This will:
# 1. Delete current configuration
# 2. Run first-time setup again
# 3. Save new preferences
```

### Manual Edit

You can manually edit `~/.goal`:

```json
{
  "author_name": "Your Name",
  "author_email": "your@email.com",
  "license": "MIT",
  "license_name": "MIT License",
  "license_classifier": "License :: OSI Approved :: MIT License"
}
```

## Supported Licenses

| # | License | SPDX ID | Use Case |
|---|---------|---------|----------|
| 1 | Apache License 2.0 | Apache-2.0 | Permissive, patent protection |
| 2 | MIT License | MIT | Simple, permissive |
| 3 | GNU GPL v3.0 | GPL-3.0 | Strong copyleft |
| 4 | BSD 3-Clause | BSD-3-Clause | Permissive, academia |
| 5 | GNU GPL v2.0 | GPL-2.0 | Legacy copyleft |
| 6 | GNU LGPL v3.0 | LGPL-3.0 | Library copyleft |
| 7 | GNU AGPL v3.0 | AGPL-3.0 | Network copyleft |
| 8 | Mozilla Public License 2.0 | MPL-2.0 | Weak copyleft |

### License Badge Formats

Each license gets an appropriate badge:

- **Apache-2.0**: Blue badge
- **MIT**: Yellow badge
- **GPL**: Blue badge
- **BSD**: Blue badge
- **MPL**: Bright green badge

## Common Workflows

### New Project Setup

```bash
# 1. Initialize git
git init
git config user.name "Tom Sapletta"
git config user.email "info@softreck.com"

# 2. Run goal (first time will configure)
goal init

# 3. Everything is automatically set up!
```

### Contributing to Existing Project

```bash
# 1. Clone the repository
git clone https://github.com/org/project.git
cd project

# 2. Make your changes
# Edit files...

# 3. Run goal
goal

# Goal will:
# - Keep existing authors
# - Add you as co-author
# - Use your license preference for new files
```

### Team Development

```bash
# Each team member runs:
goal config

# Their settings are stored locally in ~/.goal
# Project files get updated with all contributors
```

## Troubleshooting

### Git User Not Configured

**Problem**: Goal can't detect git user information

**Solution**:
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### Wrong Author in Configuration

**Problem**: You want to change your author information

**Solution**:
```bash
# Option 1: Reset and reconfigure
goal config --reset

# Option 2: Edit ~/.goal manually
nano ~/.goal
```

### License Not Updating

**Problem**: Project files not getting license updates

**Solution**:
1. Check file format is supported (pyproject.toml, package.json, Cargo.toml)
2. Ensure you have write permissions
3. Check the file syntax is valid
4. Run with debug: `goal --dry-run`

### Multiple Authors Not Working

**Problem**: Existing authors being replaced

**Solution**: This shouldn't happen - Goal always adds authors. If it does:
1. Check your Goal version: `goal --version`
2. Update to latest: `pip install --upgrade goal`
3. Report the issue on GitHub

### README Not Updating

**Problem**: README.md not getting badge updates

**Solution**:
1. Ensure README.md exists
2. Check for existing license badge format
3. Manually add a license badge if none exists
4. Goal will update it on next run

## Best Practices

### For Individual Developers

1. **Configure once**: Set up your ~/.goal on each machine
2. **Keep consistent**: Use the same email across all projects
3. **Choose wisely**: Pick a license that matches your project goals

### For Teams

1. **Respect existing authors**: Goal preserves all contributors
2. **Use standard formats**: Stick to pyproject.toml, package.json patterns
3. **Document choices**: Add LICENSE file explaining the license choice

### For Open Source Projects

1. **Add LICENSE file**: Goal updates metadata but you need the actual license text
2. **Update CONTRIBUTING.md**: Explain how authors are managed
3. **Be transparent**: Document license choice in README

## Configuration File Reference

### ~/.goal Structure

```json
{
  "author_name": "string",           // Your full name
  "author_email": "string",          // Your email address
  "license": "string",               // SPDX license identifier
  "license_name": "string",          // Human-readable license name
  "license_classifier": "string"     // PyPI classifier for license
}
```

### Example Configurations

#### Apache-2.0
```json
{
  "author_name": "Tom Sapletta",
  "author_email": "info@softreck.com",
  "license": "Apache-2.0",
  "license_name": "Apache License 2.0",
  "license_classifier": "License :: OSI Approved :: Apache Software License"
}
```

#### MIT
```json
{
  "author_name": "Jane Developer",
  "author_email": "jane@example.com",
  "license": "MIT",
  "license_name": "MIT License",
  "license_classifier": "License :: OSI Approved :: MIT License"
}
```

## Advanced Usage

### Programmatic Access

You can access user config in Python:

```python
from goal.user_config import get_user_config

config = get_user_config()
print(config.get('author_name'))
print(config.get('license'))
```

### CI/CD Integration

For CI/CD, pre-configure ~/.goal:

```yaml
# .github/workflows/release.yml
- name: Setup Goal Config
  run: |
    cat > ~/.goal << EOF
    {
      "author_name": "${{ secrets.AUTHOR_NAME }}",
      "author_email": "${{ secrets.AUTHOR_EMAIL }}",
      "license": "Apache-2.0",
      "license_name": "Apache License 2.0",
      "license_classifier": "License :: OSI Approved :: Apache Software License"
    }
    EOF

- name: Run Goal
  run: goal --all
```

## FAQ

**Q: Does Goal modify LICENSE files?**
A: No, Goal only updates project metadata files (pyproject.toml, package.json, etc.) and README badges. You need to add the LICENSE file yourself.

**Q: Can I use different licenses for different projects?**
A: Yes, the license in ~/.goal is just your default preference. Each project can have its own license, and Goal will respect it while adding you as an author.

**Q: What if I want to change my email?**
A: Run `goal config --reset` or edit ~/.goal manually.

**Q: Does this work with Poetry/npm/cargo?**
A: Yes! Goal updates the underlying project files (pyproject.toml, package.json, Cargo.toml) which are used by these tools.

**Q: Can I disable automatic metadata updates?**
A: Currently no, but you can skip specific files by not including them in your commits.

## See Also

- [Commands Reference](commands.md) - All Goal commands
- [Configuration Guide](configuration.md) - goal.yaml settings
- [CI/CD Integration](ci-cd.md) - Automated workflows
- [Examples](examples.md) - Real-world usage patterns
