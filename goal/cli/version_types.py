"""Version management - project type definitions."""

# Project type definitions with version patterns
PROJECT_TYPES = {
    "python": {
        "files": [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "Pipfile",
            "environment.yml",
            "poetry.lock",
            "uv.lock",
            "Pipfile.lock",
        ],
        "version_patterns": {
            "pyproject.toml": r'^version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            "setup.py": r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            "setup.cfg": r"^version\s*=\s*(\d+\.\d+\.\d+)",
        },
        "test_command": "python -m pytest",
        "publish_command": "python -m build && python -m twine upload --skip-existing dist/*",
    },
    "nodejs": {
        "files": [
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "bun.lockb",
        ],
        "version_patterns": {
            "package.json": r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
        },
        "test_command": "npm test",
        "publish_command": "npm publish",
    },
    "rust": {
        "files": ["Cargo.toml", "Cargo.lock"],
        "version_patterns": {
            "Cargo.toml": r'^version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        "test_command": "cargo test",
        "publish_command": "cargo publish",
    },
    "go": {
        "files": ["go.mod", "go.sum"],
        "version_patterns": {},  # Go uses git tags
        "test_command": "go test ./...",
        "publish_command": "git push origin --tags",
    },
    "ruby": {
        "files": ["Gemfile", "*.gemspec", "Gemfile.lock"],
        "version_patterns": {
            "*.gemspec": r'\.version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
        },
        "test_command": "bundle exec rspec",
        "publish_command": "gem build *.gemspec && gem push *.gem",
    },
    "php": {
        "files": ["composer.json", "composer.lock"],
        "version_patterns": {
            "composer.json": r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
        },
        "test_command": "composer test",
        "publish_command": "composer publish",
    },
    "dotnet": {
        "files": ["*.csproj", "*.fsproj", "packages.lock.json"],
        "version_patterns": {
            "*.csproj": r"<Version>(\d+\.\d+\.\d+)</Version>",
            "*.fsproj": r"<Version>(\d+\.\d+\.\d+)</Version>",
        },
        "test_command": "dotnet test",
        "publish_command": "dotnet pack && dotnet nuget push *.nupkg",
    },
    "java": {
        "files": ["pom.xml", "build.gradle", "build.gradle.kts", "gradle.lockfile"],
        "version_patterns": {
            "pom.xml": r"<version>(\d+\.\d+\.\d+)</version>",
            "build.gradle": r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']',
            "build.gradle.kts": r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        "test_command": "mvn test",
        "publish_command": "mvn deploy",
    },
    "elixir": {
        "files": ["mix.exs", "mix.lock"],
        "version_patterns": {
            "mix.exs": r'version:\s*"(\d+\.\d+\.\d+)"',
        },
        "test_command": "mix test",
        "publish_command": "mix hex.publish",
    },
    "haskell": {
        "files": [
            "*.cabal",
            "cabal.project",
            "cabal.project.freeze",
            "stack.yaml",
            "stack.yaml.lock",
        ],
        "version_patterns": {
            "*.cabal": r"version:\s*(\d+\.\d+\.\d+)",
            "cabal.project": r"version:\s*(\d+\.\d+\.\d+)",
        },
        "test_command": "cabal test",
        "publish_command": "cabal sdist",
    },
    "swift": {
        "files": ["Package.swift", "Package.resolved"],
        "version_patterns": {
            "Package.swift": r'let version = "(\d+\.\d+\.\d+)"',
        },
        "test_command": "swift test",
        "publish_command": "swift package publish",
    },
    "dart": {
        "files": ["pubspec.yaml", "pubspec.lock"],
        "version_patterns": {
            "pubspec.yaml": r"^version:\s*(\d+\.\d+\.\d+)",
        },
        "test_command": "dart test",
        "publish_command": "pub publish",
    },
    "kotlin": {
        "files": ["build.gradle.kts"],
        "version_patterns": {
            "build.gradle.kts": r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        },
        "test_command": "gradle test",
        "publish_command": "gradle publish",
    },
}
