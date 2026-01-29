# Installation

## Requirements

- Python 3.8 or higher
- Git repository

## Install from PyPI

```bash
pip install goal
```

## Install from Source

```bash
git clone https://github.com/wronai/goal.git
cd goal
pip install -e .
```

## Development Installation

```bash
git clone https://github.com/wronai/goal.git
cd goal
pip install -e ".[dev]"
```

This installs additional development dependencies:
- pytest - for testing
- build - for building packages
- twine - for publishing to PyPI

## Verify Installation

```bash
goal --version
# Goal, version 2.1.1

goal --help
# Usage: goal [OPTIONS] COMMAND [ARGS]...
```

## Optional Dependencies

Goal works out of the box, but you might want these for specific features:

### For Python Projects
```bash
pip install pytest black isort flake8
```

### For Node.js Projects
```bash
npm install -g
# Goal will use npm commands if package.json exists
```

### For Rust Projects
```bash
# Install Rust first: https://rustup.rs/
# Goal will use cargo commands if Cargo.toml exists
```

## Shell Completion

### Bash
```bash
eval "$(_GOAL_COMPLETE=bash_source goal)"
```

Add to `~/.bashrc` for permanent completion:
```bash
echo 'eval "$(_GOAL_COMPLETE=bash_source goal)"' >> ~/.bashrc
```

### Zsh
```bash
eval "$(_GOAL_COMPLETE=zsh_source goal)"
```

Add to `~/.zshrc` for permanent completion:
```bash
echo 'eval "$(_GOAL_COMPLETE=zsh_source goal)"' >> ~/.zshrc
```

### Fish
```bash
eval (env _GOAL_COMPLETE=fish_source goal)
```

## Docker

### Using Goal in Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Install Goal
RUN pip install goal

# Set up entrypoint
ENTRYPOINT ["goal"]
CMD ["--help"]
```

### Pre-built Docker Image
```bash
docker run --rm -v $(pwd):/app -w /app wronai/goal:latest push
```

## Troubleshooting

### Permission Denied

If you get a permission error, you might need to install with user permissions:

```bash
pip install --user goal
```

Make sure `~/.local/bin` is in your PATH:

```bash
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Git Not Found

Goal requires Git to be installed:

```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Windows
# Download from https://git-scm.com/
```

### Python Version

Check your Python version:

```bash
python --version
# Should be 3.8 or higher
```

If you have multiple Python versions:

```bash
python3 -m pip install goal
```

## Next Steps

After installation:

1. [Initialize your project](quickstart.md)
2. [Configure Goal](configuration.md)
3. [Check examples](examples.md)
