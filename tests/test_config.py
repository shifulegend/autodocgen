"""Tests for configuration loading."""
import os
import pytest
import tempfile
from pathlib import Path
from autodocgen.config import Config


def test_default_config():
    """Test default configuration values."""
    cfg = Config()
    assert cfg.openai_api_key is None
    assert cfg.openai_model == "gpt-4o"
    assert cfg.output_dir == "docs"
    assert cfg.source_paths == ["."]
    assert "venv" in cfg.exclude_patterns


def test_config_requires_api_key(monkeypatch):
    """Test that loading config without API key raises error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OpenAI API key not found"):
        Config.load()


def test_config_loads_from_env(monkeypatch):
    """Test that OPENAI_API_KEY environment variable is read."""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key-123")
    cfg = Config.load()
    assert cfg.openai_api_key == "env-key-123"


def test_config_loads_from_pyproject(tmp_path):
    """Test loading configuration from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[tool.autodocgen]
openai = { api_key = "file-key", model = "gpt-3.5-turbo" }
output = { dir = "custom_docs" }
source = "src"
""")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        cfg = Config.load()
        assert cfg.openai_api_key == "file-key"
        assert cfg.openai_model == "gpt-3.5-turbo"
        assert cfg.output_dir == "custom_docs"
        assert cfg.source_paths == ["src"]
    finally:
        os.chdir(old_cwd)


def test_config_loads_from_yaml(tmp_path, monkeypatch):
    """Test loading configuration from autodocgen.yaml."""
    yaml_file = tmp_path / "autodocgen.yaml"
    yaml_file.write_text("""
openai:
  api_key: yaml-key
  model: gpt-4
output:
  dir: yaml_docs
source:
  - lib
  - tests
exclude:
  - docs
  - examples
""")
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # No environment variable set - should load from YAML when explicitly passed
        cfg = Config.load(config_path=yaml_file)
        assert cfg.openai_api_key == "yaml-key"
        assert cfg.openai_model == "gpt-4"
        assert cfg.output_dir == "yaml_docs"
        assert cfg.source_paths == ["lib", "tests"]
        assert "docs" in cfg.exclude_patterns
        assert "examples" in cfg.exclude_patterns
    finally:
        os.chdir(old_cwd)


def test_config_overrides_from_cli(monkeypatch):
    """Test command-line overrides."""
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    cfg = Config.load(overrides={"output": {"dir": "cli_docs"}, "source": "src/cli"})
    assert cfg.output_dir == "cli_docs"
    assert cfg.source_paths == ["src/cli"]


def test_config_env_overrides_file(monkeypatch):
    """Test that environment variable overrides file config."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[tool.autodocgen]
openai = { api_key = "file-key", model = "gpt-3.5" }
""")
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            monkeypatch.setenv("OPENAI_API_KEY", "env-override")
            cfg = Config.load()
            assert cfg.openai_api_key == "env-override"
            # Other settings from file should still apply
            assert cfg.openai_model == "gpt-3.5"
        finally:
            os.chdir(old_cwd)
