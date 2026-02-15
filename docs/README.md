# Goal Documentation

Welcome to the Goal documentation! Goal is an automated git push tool with **enterprise-grade commit intelligence**, smart changelog updates, and version tagging.

## 🚀 What's New in v2.1

- **[Enhanced Summary Engine](enhanced-summary.md)** - Business-value focused commit messages
- **Capability Detection** - Maps code patterns to functional values
- **Relation Mapping** - `config→cli→generator` dependency chains
- **Quality Metrics** - Complexity, coverage, value scores

## 📚 Documentation Menu

### Getting Started
| Guide | Description |
|-------|-------------|
| [Installation](installation.md) | How to install Goal |
| [Quick Start](quickstart.md) | Get started in 5 minutes |
| [Basic Usage](usage.md) | Common commands and workflows |

### Configuration
| Guide | Description |
|-------|-------------|
| **[User Configuration](user-config.md)** | 🆕 Auto-detect git user & license preferences |
| [Configuration Guide](configuration.md) | Complete goal.yaml reference |
| [Project Strategies](strategies.md) | Configure for Python, Node.js, Rust |
| [Registry Setup](registries.md) | Configure PyPI, npm, crates.io |

### Enterprise Features
| Guide | Description |
|-------|-------------|
| **[Enhanced Summary](enhanced-summary.md)** | 🆕 Business-value commit messages |
| [Markdown Output](markdown-output.md) | Structured output for LLMs/automation |
| [Hooks](hooks.md) | Pre/post commit and push hooks |
| [CI/CD Integration](ci-cd.md) | GitHub Actions, GitLab CI |

### Examples & Reference
| Guide | Description |
|-------|-------------|
| [Examples](examples.md) | Real-world usage patterns |
| [Command Reference](commands.md) | All commands and options |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [FAQ](faq.md) | Frequently asked questions |

## 📂 Code & Examples

### Source Code
| File | Purpose |
|------|---------|
| [`goal/deep_analyzer.py`](../goal/deep_analyzer.py) | AST-based code analysis |
| [`goal/enhanced_summary.py`](../goal/enhanced_summary.py) | Business value extraction |
| [`goal/commit_generator.py`](../goal/commit_generator.py) | Commit message orchestration |
| [`goal/config.py`](../goal/config.py) | Configuration & quality thresholds |

### Example Projects
| Example | Description |
|---------|-------------|
| [`examples/python-package/`](../examples/python-package/) | Python package workflow |
| [`examples/nodejs-app/`](../examples/nodejs-app/) | Node.js application |
| [`examples/rust-crate/`](../examples/rust-crate/) | Rust crate publishing |
| [`examples/github-actions/`](../examples/github-actions/) | CI/CD automation |
| [`examples/git-hooks/`](../examples/git-hooks/) | Pre-commit validation |

## 🔗 Quick Links

- [GitHub Repository](https://github.com/wronai/goal)
- [PyPI Package](https://pypi.org/project/goal/)
- [Issue Tracker](https://github.com/wronai/goal/issues)
- [Changelog](../CHANGELOG.md)

## 🏆 Comparison with Alternatives

| Feature | Goal | Conventional Changelog | CodeClimate | Semantic Release |
|---------|------|----------------------|-------------|------------------|
| Business Value Titles | ✅ | ❌ | ❌ | ❌ |
| Capability Detection | ✅ | ❌ | ⚠️ | ❌ |
| Relation Mapping | ✅ | ❌ | ✅ | ❌ |
| Quality Metrics | ✅ | ❌ | ✅ | ❌ |
| Zero Config | ✅ | ⚠️ | ❌ | ⚠️ |
| Multi-language | ✅ | ⚠️ | ✅ | ⚠️ |

See [Enhanced Summary](enhanced-summary.md#comparison-with-alternatives) for detailed comparison.

## 🔗 Quick Links

- [GitHub Repository](https://github.com/wronai/goal)
- [PyPI Package](https://pypi.org/project/goal/)
- [Issue Tracker](https://github.com/wronai/goal/issues)

## 📖 Table of Contents

```toc
# Goal Documentation
## Getting Started
### Installation
### Quick Start
### Basic Usage
## Configuration
### Configuration Guide
### Project Strategies
### Registry Setup
## Advanced Features
### Examples
### Hooks
### CI/CD Integration
### Markdown Output
## Reference
### Command Reference
### Troubleshooting
### FAQ
```
