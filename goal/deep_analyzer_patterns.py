"""Static pattern tables for deep code analysis (keeps deep_analyzer.py maintainability high)."""

VALUE_PATTERNS = {
    "configuration": {
        "signatures": ["config", "yaml", "toml", "settings", "options", "parse_config"],
        "keywords": ["load_config", "get_config", "save_config", "merge"],
        "impact": "improved configuration management",
    },
    "cli": {
        "signatures": ["click.", "@click", "argparse", "command", "option"],
        "keywords": ["add_command", "cli", "parse_args"],
        "impact": "enhanced CLI interface",
    },
    "api": {
        "signatures": ["endpoint", "route", "request", "response", "api"],
        "keywords": ["get", "post", "put", "delete", "handler"],
        "impact": "new API capabilities",
    },
    "database": {
        "signatures": ["db", "sql", "query", "model", "migrate"],
        "keywords": ["insert", "update", "delete", "select", "connection"],
        "impact": "database improvements",
    },
    "auth": {
        "signatures": ["auth", "login", "token", "permission", "session"],
        "keywords": ["authenticate", "authorize", "verify", "jwt"],
        "impact": "security enhancements",
    },
    "testing": {
        "signatures": ["test_", "assert", "mock", "fixture", "pytest"],
        "keywords": ["test", "spec", "coverage"],
        "impact": "improved test coverage",
    },
    "logging": {
        "signatures": ["log", "logger", "logging", "debug", "info"],
        "keywords": ["error", "warning", "trace"],
        "impact": "better observability",
    },
    "performance": {
        "signatures": ["cache", "async", "parallel", "optimize"],
        "keywords": ["speed", "fast", "efficient", "memory"],
        "impact": "performance improvements",
    },
    "formatting": {
        "signatures": ["format", "render", "template", "markdown", "html"],
        "keywords": ["output", "display", "style"],
        "impact": "improved output formatting",
    },
    "validation": {
        "signatures": ["valid", "check", "verify", "ensure", "sanitize"],
        "keywords": ["schema", "constraint", "rule"],
        "impact": "better input validation",
    },
}

RELATION_PATTERNS = {
    ("config", "cli"): "configuration-driven CLI",
    ("config", "core"): "configurable core logic",
    ("test", "core"): "better test coverage",
    ("docs", "core"): "improved documentation",
    ("api", "db"): "data-driven API",
    ("auth", "api"): "secure API endpoints",
}
