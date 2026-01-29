# Frequently Asked Questions

## General

### Q: What is Goal?
A: Goal is an automated git push tool that generates smart commit messages, manages versions, updates changelogs, and handles publishing to package registries.

### Q: Do I need to configure anything?
A: No! Goal works out of the box with sensible defaults. Just run `goal init` in your repository.

### Q: What programming languages does Goal support?
A: Goal supports Python, Node.js, Rust, Go, Ruby, PHP, .NET, and Java. It automatically detects your project type.

### Q: Is Goal free to use?
A: Yes, Goal is open source under the Apache 2.0 license.

## Installation

### Q: How do I install Goal?
A: `pip install goal` or install from source: `git clone https://github.com/wronai/goal.git && cd goal && pip install -e .`

### Q: What are the requirements?
A: Python 3.8+ and a git repository.

### Q: Can I use Goal in a virtual environment?
A: Yes, and it's recommended. Install it in your project's virtual environment or globally with `pip install --user goal`.

## Configuration

### Q: Do I need a goal.yaml file?
A: It's optional but recommended. Run `goal init` to create one with auto-detected settings.

### Q: Where does Goal look for goal.yaml?
A: In order: 1) Path specified with `--config`, 2) Current directory, 3) Parent directories up to git root.

### Q: Can I have multiple configurations?
A: Yes! Use `goal --config staging.yaml` for different environments.

### Q: How do I configure custom test commands?
A: `goal config set strategies.python.test "pytest -xvs --cov"`

## Usage

### Q: What's the difference between `goal` and `goal push`?
A: `goal` is an alias for `goal push`. Both do the same thing.

### Q: How does Goal generate commit messages?
A: It analyzes your changes using file patterns, diff content, and heuristics to determine the type (feat/fix/docs/etc) and generates a conventional commit message.

### Q: Can I use my own commit message?
A: Yes: `goal push -m "your custom message"`

### Q: What are version bumps?
A: Goal can automatically increment your version: patch (1.0.0→1.0.1), minor (1.0.0→1.1.0), or major (1.0.0→2.0.0).

### Q: How do I skip the prompts?
A: Use `goal --yes` for automatic mode or `goal --all` for full automation including publishing.

## Git Integration

### Q: Does Goal work with any git repository?
A: Yes, as long as it's a valid git repository.

### Q: Can I use Goal with GitHub, GitLab, Bitbucket?
A: Yes, Goal works with any git hosting service.

### Q: What if I already have git hooks?
A: Goal hooks don't interfere with git hooks. You can use them together or call git hooks from Goal hooks.

### Q: Can Goal handle merge conflicts?
A: No, you need to resolve merge conflicts manually before running Goal.

## Version Management

### Q: What version files does Goal update?
A: By default: VERSION, pyproject.toml, package.json, Cargo.toml, setup.py. You can customize this in goal.yaml.

### Q: How does version bumping work?
A: Based on the number of files changed and lines added/removed. You can configure thresholds in goal.yaml.

### Q: Can I use calendar versioning (CalVer)?
A: Yes: `goal config set versioning.strategy "calver"`

### Q: What if my version format is custom?
A: You can customize version files and patterns in goal.yaml.

## Publishing

### Q: Where can Goal publish?
A: PyPI, npm, crates.io, RubyGems, and any custom registry you configure.

### Q: How do I set up publishing tokens?
A: Set environment variables like `PYPI_TOKEN`, `NPM_TOKEN`, etc. See the [Registry Configuration](registries.md) guide.

### Q: Can Goal publish to multiple registries?
A: Yes, configure multiple registries and use custom publish commands.

### Q: What if I don't want to publish?
A: Use `goal push --no-publish` or don't configure publishing.

## CI/CD

### Q: Can I use Goal in GitHub Actions?
A: Yes! See the [CI/CD Integration](ci-cd.md) guide for examples.

### Q: How do I handle authentication in CI?
A: Use repository secrets or environment variables for tokens.

### Q: Can Goal run in Docker?
A: Yes, `docker run --rm -v $(pwd):/app -w /app goal push`

### Q: What about GitLab CI or Jenkins?
A: Goal works with any CI/CD system. See examples in the documentation.

## Advanced Features

### Q: What are split commits?
A: `goal push --split` creates separate commits for different types of changes (code, docs, ci, etc).

### Q: How do ticket prefixes work?
A: Create a TICKET file with `prefix=ABC-123` or use `goal --ticket JIRA-456`

### Q: What's the difference between markdown and ASCII output?
A: Markdown output is structured and perfect for logs/LLMs, ASCII is simpler terminal output.

### Q: Can I customize commit message templates?
A: Yes: `goal config set git.commit.templates.feat "✨ {scope}: {description}"`

## Troubleshooting

### Q: Goal says "No changes to commit"
A: Stage your changes first: `git add .`

### Q: Tests are failing but I want to continue
A: Goal will prompt you. Type 'y' to continue or use `goal push --yes -m "fix: critical"`

### Q: My version isn't updating in all files
A: Check `goal config get versioning.files` and run `goal config update`

### Q: Publish is failing with authentication error
A: Check your environment variables: `echo $PYPI_TOKEN`

## Comparison

### Q: How is Goal different from `semantic-release`?
A: Goal is simpler, works without configuration, and focuses on interactive use with smart commit generation.

### Q: Goal vs `standard-version`?
A: Goal includes git operations, testing, and publishing out of the box, while standard-version focuses on versioning and changelog.

### Q: Why not just use git directly?
A: Goal automates the entire workflow: commit messages, version bumping, changelog, tagging, pushing, and publishing in one command.

## Best Practices

### Q: Should I commit goal.yaml?
A: Yes, commit it so your team uses the same configuration.

### Q: How often should I run Goal?
A: Whenever you have changes to commit and push. For releases, use `goal --all`.

### Q: Should I use Goal for hotfixes?
A: Yes, but consider `goal push --bump patch -m "fix: critical bug"`

### Q: Can I use Goal in a monorepo?
A: Yes, configure multiple strategies and version files for each package.

## Contributing

### Q: How can I contribute to Goal?
A: Check the [contributing guide](https://github.com/wronai/goal/blob/main/CONTRIBUTING.md) on GitHub.

### Q: Where do I report bugs?
A: Open an issue on [GitHub Issues](https://github.com/wronai/goal/issues).

### Q: Can I request features?
A: Yes! Open an issue with the "enhancement" label.

## Miscellaneous

### Q: Does Goal work on Windows?
A: Yes, it works on Windows, macOS, and Linux.

### Q: Can I use Goal with LFS (Large File Storage)?
A: Yes, Goal works with any git repository including those using LFS.

### Q: Is there a GUI for Goal?
A: No, Goal is command-line only to keep it simple and scriptable.

### Q: Can I disable the changelog?
A: Yes: `goal config set git.changelog.enabled false` or use `goal push --no-changelog`

## Still Have Questions?

- Check the [troubleshooting guide](troubleshooting.md)
- Look at [examples](examples.md)
- Open a [GitHub discussion](https://github.com/wronai/goal/discussions)
- Create an [issue](https://github.com/wronai/goal/issues)
