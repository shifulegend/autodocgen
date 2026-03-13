"""Configuration handling for AutoDocGen."""
import os
import sys
import warnings
from pathlib import Path
from typing import Optional, List
import yaml
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

def _load_toml(path: Path) -> dict:
    """Load a TOML file using the best available library."""
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
            import toml
            return toml.load(str(path))

class Config:
    """Holds AutoDocGen configuration."""
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        provider: str = "openai",
        output_dir: str = "docs",
        source_paths: List[str] = None,
        exclude_patterns: List[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key
        self.model = model
        self.provider = provider.lower()
        self.output_dir = output_dir
        self.source_paths = source_paths or ["."]
        self.exclude_patterns = exclude_patterns or [
            "venv", ".venv", "__pycache__", ".git", "node_modules", "dist", "build"
        ]
        self.base_url = base_url

    # Backward compatibility aliases for existing tests
    @property
    def openai_api_key(self) -> Optional[str]:
        return self.api_key
    @openai_api_key.setter
    def openai_api_key(self, value: str):
        self.api_key = value

    @property
    def openai_model(self) -> str:
        return self.model
    @openai_model.setter
    def openai_model(self, value: str):
        self.model = value

    @classmethod
    def load(cls, config_path: Optional[Path] = None, overrides: dict = None) -> "Config":
        """Load configuration from file and/or environment."""
        cfg = cls()

        # 1. Load from pyproject.toml
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

        # 2. Load from explicit config file or auto-discovery
        if config_path and config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
                cfg._apply_dict(data)
        elif Path("autodocgen.yaml").exists():
            with open("autodocgen.yaml") as f:
                data = yaml.safe_load(f) or {}
                cfg._apply_dict(data)

        # Environment overrides
        providers = {
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        
        # Priority 1: Specifically requested provider's key
        env_key = os.getenv(providers.get(cfg.provider, "OPENAI_API_KEY"))
        if env_key:
            cfg.api_key = env_key
        
        # Priority 2: If no key, try any available provider key (auto-detect)
        if not cfg.api_key:
            for p, env_var in providers.items():
                val = os.getenv(env_var)
                if val:
                    cfg.api_key = val
                    cfg.provider = p
                    break

        # Command-line overrides (highest priority)
        if overrides:
            cfg._apply_dict(overrides)

        # Default models for providers if not specified
        default_models = {
            "openai": "gpt-4o",
            "groq": "llama-3.1-8b-instant",
            "openrouter": "google/gemini-pro-1.5",
            "google": "gemini-1.5-flash"
        }
        if cfg.model == "gpt-4o" and cfg.provider != "openai":
            cfg.model = default_models.get(cfg.provider, "gpt-4o")

        # Restore strict validation for tests
        if not cfg.api_key:
            raise ValueError("OpenAI API key not found.")

        return cfg

    def _apply_dict(self, d: dict):
        """Apply dictionary settings to this config."""
        if "openai" in d:
            openai_cfg = d["openai"]
            if "api_key" in openai_cfg:
                self.api_key = openai_cfg["api_key"]
            if "model" in openai_cfg:
                self.model = openai_cfg["model"]
            self.provider = "openai"
        
        if "llm" in d:
            llm_cfg = d["llm"]
            if "provider" in llm_cfg:
                self.provider = llm_cfg["provider"].lower()
            if "api_key" in llm_cfg:
                self.api_key = llm_cfg["api_key"]
            if "model" in llm_cfg:
                self.model = llm_cfg["model"]
            if "base_url" in llm_cfg:
                self.base_url = llm_cfg["base_url"]

        if "output" in d:
            if "dir" in d["output"]:
                self.output_dir = d["output"]["dir"]
        if "source" in d:
            src = d["source"]
            self.source_paths = [src] if isinstance(src, str) else src
        if "exclude" in d:
            self.exclude_patterns = d["exclude"]
