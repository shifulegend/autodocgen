"""Configuration handling for AutoDocGen."""
import os
from pathlib import Path
from typing import Optional
import yaml


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
        """
        Load configuration from file and/or environment.
        Search order:
        1. Explicit config_path if provided
        2. pyproject.toml [tool.autodocgen] section
        3. autodocgen.yaml in current directory
        Environment variable: OPENAI_API_KEY overrides any file setting for API key.
        """
        # Start with defaults
        cfg = cls()

        # Load from pyproject.toml if exists
        pyproject = Path("pyproject.toml")
        if pyproject.exists():
            import toml
            try:
                data = toml.load(pyproject)
                tool_cfg = data.get("tool", {}).get("autodocgen", {})
                if tool_cfg:
                    cfg._apply_dict(tool_cfg)
            except Exception:
                pass  # ignore malformed pyproject

        # Load from explicit config file (YAML)
        if config_path and config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
                cfg._apply_dict(data)

        # Environment overrides
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
            # can be a string or list
            src = d["source"]
            self.source_paths = [src] if isinstance(src, str) else src
        if "exclude" in d:
            self.exclude_patterns = d["exclude"]