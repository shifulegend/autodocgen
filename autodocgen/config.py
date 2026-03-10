"""Configuration handling for AutoDocGen."""
import os
import sys
import warnings
from pathlib import Path
from typing import Optional
import yaml


def _load_toml(path: Path) -> dict:
    """Load a TOML file using the best available library.

    Uses the stdlib tomllib on Python 3.11+, or the tomli backport on 3.10.
    """
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, 'rb') as f:
            return tomllib.load(f)
    else:
        try:
            import tomli
            with open(path, 'rb') as f:
                return tomli.load(f)
        except ImportError:
            # Fallback to the older 'toml' package if tomli is not installed
            import toml
            return toml.load(str(path))


class Config:
    """Holds AutoDocGen configuration."""
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o",
        output_dir: str = "docs",
        source_paths: list[str] = None,
        exclude_patterns: list[str] = None,
    ):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.output_dir = output_dir
        self.source_paths = source_paths or ["."]
        self.exclude_patterns = exclude_patterns or [
            "venv", ".venv", "__pycache__", ".git", "node_modules", "dist", "build"
        ]

    @classmethod
    def load(cls, config_path: Optional[Path] = None, overrides: dict = None) -> "Config":
        """Load configuration from file and/or environment.

        Search order:
        1. ``pyproject.toml`` [tool.autodocgen] section in the current directory
        2. Explicit ``config_path`` if provided (YAML format)
        3. ``autodocgen.yaml`` auto-discovered in the current directory
        Environment variable ``OPENAI_API_KEY`` always takes precedence over file values.
        """
        cfg = cls()

        # 1. Load from pyproject.toml if it exists in the current directory
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            try:
                data = _load_toml(pyproject)
                tool_cfg = data.get("tool", {}).get("autodocgen", {})
                if tool_cfg:
                    cfg._apply_dict(tool_cfg)
            except Exception as exc:
                warnings.warn(
                    f"Could not parse pyproject.toml for [tool.autodocgen]: {exc}",
                    stacklevel=2,
                )

        # 2. Auto-discover autodocgen.yaml in the current directory
        auto_yaml = Path("autodocgen.yaml")
        if auto_yaml.exists() and config_path is None:
            with open(auto_yaml) as f:
                data = yaml.safe_load(f) or {}
                cfg._apply_dict(data)

        # 3. Load from explicit config file (YAML), overrides auto-discovery
        if config_path and config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
                cfg._apply_dict(data)

        # Environment overrides (highest priority for API key)
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            cfg.openai_api_key = env_key

        # Command-line overrides
        if overrides:
            cfg._apply_dict(overrides)

        # Validate required fields
        if not cfg.openai_api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable or provide in config."
            )

        return cfg

    def _apply_dict(self, d: dict):
        """Apply dictionary settings to this config."""
        if "openai" in d:
            openai_cfg = d["openai"]
            if "api_key" in openai_cfg:
                self.openai_api_key = openai_cfg["api_key"]
            if "model" in openai_cfg:
                self.openai_model = openai_cfg["model"]
        if "output" in d:
            if "dir" in d["output"]:
                self.output_dir = d["output"]["dir"]
        if "source" in d:
            src = d["source"]
            self.source_paths = [src] if isinstance(src, str) else src
        if "exclude" in d:
            self.exclude_patterns = d["exclude"]
