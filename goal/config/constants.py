"""Goal configuration constants - default configuration template."""

# Default configuration template
DEFAULT_CONFIG = {
    "version": "1.0",
    "project": {
        "name": "",
        "type": [],
        "description": "",
    },
    "versioning": {
        "strategy": "semver",
        "files": [
            "VERSION",
            "pyproject.toml:version",
        ],
        "bump_rules": {
            "patch": 10,
            "minor": 50,
            "major": 200,
        },
    },
    "git": {
        "commit": {
            "strategy": "conventional",
            "scope": "",
            "abstraction_level": "auto",  # auto, high, medium, low
            "abstraction_levels": {
                "high": "{type}({domain}): {benefit}",
                "medium": "{type}({domain}): {action} {entities}",
                "low": "{type}({domain}): update {file_count} files (+{added}/-{deleted})",
            },
            "domain_mapping": {
                "goal/*.py": "core",
                "src/*.py": "core",
                "lib/*.py": "core",
                "app/*.py": "app",
                "api/*.py": "api",
                "docs/*": "docs",
                "tests/*": "test",
                "test/*": "test",
                "*.md": "docs",
                "*.rst": "docs",
                "pyproject.toml": "build",
                "setup.py": "build",
                "setup.cfg": "build",
                "package.json": "build",
                "Cargo.toml": "build",
                "goal.yaml": "config",
                ".github/*": "ci",
                ".gitlab-ci.yml": "ci",
                "Dockerfile": "docker",
                "docker-compose.yml": "docker",
            },
            "benefit_keywords": {
                "config": "better configuration management",
                "cli": "improved CLI experience",
                "api": "enhanced API functionality",
                "test": "improved test coverage",
                "docs": "better documentation",
                "auth": "enhanced security",
                "perf": "improved performance",
                "refactor": "cleaner code architecture",
                "fix": "resolved issues",
                "feat": "new functionality",
            },
            "templates": {
                "feat": {
                    "high": "feat({domain}): {benefit}",
                    "medium": "feat({domain}): add {entities}",
                    "low": "feat({domain}): add {file_count} files (+{added}/-{deleted})",
                },
                "fix": {
                    "high": "fix({domain}): {benefit}",
                    "medium": "fix({domain}): resolve {entities}",
                    "low": "fix({domain}): update {file_count} files (+{added}/-{deleted})",
                },
                "docs": {
                    "high": "docs({domain}): {benefit}",
                    "medium": "docs({domain}): document {entities}",
                    "low": "docs({domain}): update {file_count} files",
                },
                "refactor": {
                    "high": "refactor({domain}): {benefit}",
                    "medium": "refactor({domain}): restructure {entities}",
                    "low": "refactor({domain}): update {file_count} files",
                },
                "test": {
                    "high": "test({domain}): {benefit}",
                    "medium": "test({domain}): add tests for {entities}",
                    "low": "test({domain}): update {file_count} files",
                },
                "build": {
                    "high": "build({domain}): {benefit}",
                    "medium": "build({domain}): configure {entities}",
                    "low": "build({domain}): update {file_count} files",
                },
                "chore": {
                    "high": "chore({domain}): {benefit}",
                    "medium": "chore({domain}): update {entities}",
                    "low": "chore({domain}): update {file_count} files",
                },
                "style": {
                    "high": "style({domain}): {benefit}",
                    "medium": "style({domain}): format {entities}",
                    "low": "style({domain}): update {file_count} files",
                },
                "perf": {
                    "high": "perf({domain}): {benefit}",
                    "medium": "perf({domain}): optimize {entities}",
                    "low": "perf({domain}): update {file_count} files",
                },
            },
            "classify_by": [
                "file_extensions",
                "directory_paths",
                "line_stats",
                "keywords_diff",
                "code_entities",
            ],
            "value_patterns": {
                "configuration": {
                    "signatures": ["config", "yaml", "toml", "settings", "options"],
                    "impact": "better configuration management",
                    "changelog_section": "core",
                },
                "cli": {
                    "signatures": ["click.", "@click", "command", "option", "argparse"],
                    "impact": "improved CLI experience",
                    "changelog_section": "core",
                },
                "api": {
                    "signatures": [
                        "endpoint",
                        "route",
                        "request",
                        "response",
                        "handler",
                    ],
                    "impact": "enhanced API functionality",
                    "changelog_section": "core",
                },
                "testing": {
                    "signatures": ["test_", "assert", "mock", "fixture", "pytest"],
                    "impact": "improved test coverage",
                    "changelog_section": "test",
                },
                "documentation": {
                    "paths": ["docs/*", "*.md", "README*"],
                    "impact": "comprehensive documentation",
                    "changelog_section": "docs",
                },
                "performance": {
                    "signatures": ["cache", "async", "parallel", "optimize", "speed"],
                    "impact": "performance improvements",
                    "changelog_section": "core",
                },
                "security": {
                    "signatures": ["auth", "token", "permission", "encrypt", "secure"],
                    "impact": "security enhancements",
                    "changelog_section": "core",
                },
                "formatting": {
                    "signatures": [
                        "format",
                        "render",
                        "template",
                        "markdown",
                        "output",
                    ],
                    "impact": "improved output formatting",
                    "changelog_section": "core",
                },
            },
            "relations": {
                "config → cli": "configuration-driven CLI",
                "config → core": "configurable core logic",
                "test → core": "better test coverage",
                "docs → core": "improved documentation",
            },
        },
        "changelog": {
            "enabled": True,
            "template": "keep-a-changelog",
            "output": "CHANGELOG.md",
            "sections": [
                "Added",
                "Changed",
                "Fixed",
                "Deprecated",
                "Removed",
                "Security",
            ],
            "group_by_domain": True,
            "domain_sections": {
                "core": ["feat", "fix", "refactor", "perf"],
                "docs": ["docs"],
                "test": ["test"],
                "build": ["build", "chore"],
                "ci": ["ci"],
            },
            "include_entities": True,
            "max_entities_per_entry": 5,
        },
        "tag": {
            "enabled": True,
            "prefix": "v",
            "format": "{prefix}{version}",
        },
    },
    "strategies": {
        "python": {
            "test": "pytest tests/ -v",
            "build": "python -m build",
            "publish": "twine upload dist/{project_name}-{version}*",  # placeholder, replaced on init
            "publish_enabled": True,
            "dependencies": {
                "file": "requirements.txt",
                "lock": "pip freeze > requirements.txt",
            },
        },
        "nodejs": {
            "test": "npm test",
            "build": "npm run build",
            "publish": "npm publish",
            "publish_enabled": True,
            "dependencies": {
                "file": "package-lock.json",
                "lock": "npm install",
            },
        },
        "rust": {
            "test": "cargo test",
            "build": "cargo build --release",
            "publish": "cargo publish",
            "publish_enabled": True,
            "dependencies": {
                "file": "Cargo.lock",
                "lock": "cargo update",
            },
        },
    },
    "registries": {
        "pypi": {
            "url": "https://pypi.org/simple/",
            "token_env": "PYPI_TOKEN",
        },
        "npm": {
            "url": "https://registry.npmjs.org/",
            "token_env": "NPM_TOKEN",
        },
    },
    "hooks": {
        "pre_commit": "",
        "post_commit": "",
        "pre_push": "",
        "post_push": "",
    },
    "advanced": {
        "auto_update_config": True,
        "performance": {
            "max_files": 50,
            "timeout_test": 300,
        },
        "file_validation": {
            "max_file_size_mb": 10,
            "block_large_files": True,
            "detect_api_tokens": True,
            "auto_manage_gitignore": True,
            "auto_add_dot_folders": True,
            "auto_handle_large_files": True,  # Auto-exclude large files
            "known_dot_folders": [
                ".idea",
                ".vscode",
                ".DS_Store",
                "Thumbs.db",
                ".pytest_cache",
                ".coverage",
                ".mypy_cache",
                ".tox",
                ".nox",
                ".venv",
                ".env",
                ".python-version",
                ".ruff_cache",
                ".cursorignore",
                ".cursorindexingignore",
                ".code2llm_cache",
                ".llm",
                "managed_components",
                ".gui-agent.pid",
                ".gui-server.pid",
                ".gui-server.log",
            ],
            "token_patterns": [
                # GitHub tokens
                r"ghp_[a-zA-Z0-9]{36}",
                r"gho_[a-zA-Z0-9]{36}",
                r"ghu_[a-zA-Z0-9]{36}",
                r"ghs_[a-zA-Z0-9]{36}",
                r"ghr_[a-zA-Z0-9]{36}",
                # GitHub app tokens
                r"ghs_[a-zA-Z0-9]{36}",
                # Generic API keys
                r"AKIA[0-9A-Z]{16}",  # AWS
                r"sk-[a-zA-Z0-9]{48}",  # Stripe
                r"xoxb-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}",  # Slack bot
                r"xoxp-[0-9]{13}-[0-9]{13}-[0-9]{13}-[a-zA-Z0-9]{24}",  # Slack user
                r"glpat-[a-zA-Z0-9_-]{20}",  # GitLab
                r"pk_live_[a-zA-Z0-9]{24}",  # Stripe publishable
                r"pk_test_[a-zA-Z0-9]{24}",  # Stripe test
                r"sk_live_[a-zA-Z0-9]{24}",  # Stripe secret
                r"sk_test_[a-zA-Z0-9]{24}",  # Stripe test
                # Generic patterns
                r"Bearer\s+[a-zA-Z0-9_-]{20,}",  # Bearer tokens
                r"Token\s+[a-zA-Z0-9_-]{20,}",  # Token auth
                # Private keys
                r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
                r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----",
                r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----",
                r"-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----",
                # .env files (check for common patterns)
                r"^[A-Z_]+=[a-zA-Z0-9_-]{20,}",  # ENV_VAR=long_value
            ],
        },
        "recovery": {
            "enabled": True,
            "auto_offer": True,  # Automatically offer recovery on push failure
            "create_backup": True,  # Create backup branch before recovery
            "clean_clone_fallback": True,  # Use clean clone method if standard recovery fails
            "strategies": {
                "auth": {
                    "enabled": True,
                    "try_gh_cli": True,
                    "try_token_auth": True,
                },
                "large_files": {
                    "enabled": True,
                    "max_size_mb": 100,  # GitHub's limit
                    "auto_lfs": False,  # Don't automatically move to LFS
                    "default_action": "remove",  # remove, lfs, or skip
                },
                "divergent_history": {
                    "enabled": True,
                    "default_action": "rebase",  # rebase, merge, or force
                    "auto_rebase": False,  # Don't auto-rebase without confirmation
                },
                "corrupted_objects": {
                    "enabled": True,
                    "run_fsck": True,
                    "run_gc": True,
                },
                "lfs": {
                    "enabled": True,
                    "auto_install": False,
                    "auto_pull": True,
                },
                "force_push": {
                    "enabled": True,
                    "require_confirmation": True,
                    "prefer_force_with_lease": True,
                },
            },
        },
    },
    "quality": {
        "commit_summary": {
            "min_value_words": 3,
            "max_generic_terms": 0,
            "required_metrics": 2,
            "relation_threshold": 0.7,
            "generic_terms": [
                "update",
                "improve",
                "enhance",
                "fix",
                "change",
                "modify",
                "cleaner",
                "better",
                "refactor",
                "misc",
            ],
        },
        "enhanced_summary": {
            "enabled": True,
            "min_capabilities": 1,
            "min_value_score": 50,
            "include_metrics": True,
            "include_relations": True,
            "include_roles": True,
        },
        "gates": {
            "max_complexity_percent": 200,
            "max_duplicate_relations": 0,
            "min_unique_files_ratio": 0.8,
            "min_capabilities": 1,
            "max_banned_words": 0,
        },
        "role_patterns": {
            r"_analyze_(python|js|generic)_diff": "language-specific code analyzer",
            r"CodeChangeAnalyzer": "AST-based change detector",
            r"analyze_file_diff": "diff analysis engine",
            r"generate_functional_summary": "business value summarizer",
            r"generate.*message": "commit message generator",
            r"EnhancedSummaryGenerator": "enterprise changelog generator",
            r"GoalConfig": "configuration manager",
            r"@click\.command": "CLI command",
            r"@click\.option": "CLI option",
            r"format_.*result": "output formatter",
            r"_calculate_complexity": "complexity analyzer",
        },
        "value_patterns": {
            "ast_analysis": {
                "signatures": ["ast.parse", "ast.walk", "libcst", "tree-sitter", "AST"],
                "capability": "deep code analysis engine",
                "impact": "intelligent change detection",
            },
            "dependency_graph": {
                "signatures": ["networkx", "relations", "dependencies", "graph"],
                "capability": "code relationship mapping",
                "impact": "architecture understanding",
            },
            "quality_metrics": {
                "signatures": ["radon", "cyclomatic", "complexity", "coverage"],
                "capability": "code quality metrics",
                "impact": "maintainability tracking",
            },
            "multi_language": {
                "signatures": ["_analyze_python", "_analyze_js", "language", "parser"],
                "capability": "multi-language support",
                "impact": "universal code analysis",
            },
        },
        "commit_message": {
            "min_length": 15,
            "max_length": 72,
            "max_entities": 5,
            "require_type": True,
            "require_scope": True,
        },
        "changelog": {
            "min_entries_per_release": 1,
            "max_file_lines": 10,
            "include_commit_hash": True,
        },
    },
    "code_parsers": {
        "python": {
            "extract": ["def ", "class ", "async def ", "@click.", "@app.", "@router."],
            "ignore": ["import ", "from ", "#", '"""', "'''"],
            "entity_pattern": r"(?:def|class|async def)\s+(\w+)",
        },
        "javascript": {
            "extract": ["function ", "const ", "class ", "export ", "async "],
            "ignore": ["import ", "//", "/*", "*/"],
            "entity_pattern": r"(?:function|class|const)\s+(\w+)",
        },
        "typescript": {
            "extract": [
                "function ",
                "const ",
                "class ",
                "interface ",
                "type ",
                "export ",
            ],
            "ignore": ["import ", "//", "/*", "*/"],
            "entity_pattern": r"(?:function|class|const|interface|type)\s+(\w+)",
        },
        "rust": {
            "extract": ["fn ", "struct ", "enum ", "impl ", "pub ", "mod "],
            "ignore": ["//", "/*", "*/"],
            "entity_pattern": r"(?:fn|struct|enum|impl|mod)\s+(\w+)",
        },
        "go": {
            "extract": ["func ", "type ", "struct ", "interface "],
            "ignore": ["//", "/*", "*/"],
            "entity_pattern": r"(?:func|type)\s+(\w+)",
        },
        "markdown": {
            "extract": ["# ", "## ", "### ", "#### ", "- **"],
            "ignore": ["<!--", "-->"],
            "entity_pattern": r"^#+\s+(.+)$",
        },
    },
}
