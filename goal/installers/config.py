"""Configuration for package manager installers from pyproject.toml."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InstallerConfig:
    """Configuration for package manager installer behavior."""
    preferred: list[str] = field(default_factory=lambda: ["uv", "pdm", "poetry", "pip"])
    auto_install_uv: bool = True
    timeout: int = 300
    default_extras: list[str] = field(default_factory=lambda: ["dev"])
    detection_cache_ttl: int = 300
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InstallerConfig":
        """Create config from dictionary (e.g., from pyproject.toml)."""
        return cls(
            preferred=data.get("preferred", ["uv", "pdm", "poetry", "pip"]),
            auto_install_uv=data.get("auto_install_uv", True),
            timeout=data.get("timeout", 300),
            default_extras=data.get("default_extras", ["dev"]),
            detection_cache_ttl=data.get("detection_cache_ttl", 300),
        )


def load_installer_config(project_dir: str = ".") -> InstallerConfig:
    """Load installer configuration from pyproject.toml."""
    pyproject = Path(project_dir) / "pyproject.toml"
    if not pyproject.exists():
        return InstallerConfig()
    
    try:
        import tomllib
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        cfg = data.get("tool", {}).get("goal", {}).get("installers", {})
        return InstallerConfig.from_dict(cfg)
    except Exception:
        return InstallerConfig()
