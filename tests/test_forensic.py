import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from autodocgen.parser import parse_file, _get_docstring
from autodocgen.scanner import scan_directory
from autodocgen.config import Config
from autodocgen.generator import AIDocGenerator
from autodocgen.writer import render_module_doc

# TC-WB-01: Verify _get_docstring correctly handles docstrings
def test_get_docstring():
    import ast
    code = '"""Module docstring."""\ndef foo():\n    """Func docstring."""\n    pass'
    tree = ast.parse(code)
    assert _get_docstring(tree) == "Module docstring."
    assert _get_docstring(tree.body[1]) == "Func docstring."

# TC-WB-02: Verify parse_file extracts class bases and method signatures
def test_parse_file_logic(tmp_path):
    code_file = tmp_path / "sample.py"
    code_file.write_text("""
class Base:
    def base_method(self, x: int):
        \"\"\"Base method doc.\"\"\"
        pass

class Derived(Base):
    def derived_method(self, y: str) -> bool:
        pass
""", encoding="utf-8")
    
    module = parse_file(code_file)
    assert module.module_name == "sample"
    assert len(module.classes) == 2
    
    base_cls = next(c for c in module.classes if c.name == "Base")
    assert base_cls.bases == []
    assert len(base_cls.methods) == 1
    assert base_cls.methods[0].name == "base_method"
    assert "x" in base_cls.methods[0].args
    
    derived_cls = next(c for c in module.classes if c.name == "Derived")
    assert derived_cls.bases == ["Base"]
    assert derived_cls.methods[0].name == "derived_method"
    assert "y" in derived_cls.methods[0].args
    assert "bool" in derived_cls.methods[0].returns

# TC-UT-01: scan_directory should skip forbidden directories
def test_scan_directory_exclusions(tmp_path):
    (tmp_path / "venv").mkdir()
    (tmp_path / "venv" / "lib.py").touch()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()
    (tmp_path / "test_file.py").touch()
    
    files = scan_directory(tmp_path)
    filenames = [f.name for f in files]
    assert "main.py" in filenames
    assert "test_file.py" in filenames
    assert "lib.py" not in filenames

# TC-UT-02: Config.load environment overrides
def test_config_env_overrides(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    # Reset any existing env vars that might interfere
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    
    cfg = Config.load(overrides={"llm": {"provider": "groq"}})
    assert cfg.api_key == "test-groq-key"
    assert cfg.provider == "groq"
    assert cfg.model == "llama-3.1-8b-instant"

# TC-FT-01: Mocked documentation generation
@patch("openai.resources.chat.completions.Completions.create")
def test_ai_generation_mock(mock_create):
    mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content="AI Generated Doc"))])
    
    gen = AIDocGenerator(api_key="fake-key", model="gpt-4o", provider="openai")
    doc = gen.generate_function_docs("my_func", ["a"], "int", "Original doc")
    
    assert doc == "AI Generated Doc"
    assert mock_create.called

# TC-API-01: Handle API errors gracefully
@patch("openai.resources.chat.completions.Completions.create")
def test_ai_generation_error(mock_create):
    mock_create.side_effect = Exception("API Connection Error")
    
    gen = AIDocGenerator(api_key="fake-key", model="gpt-4o", provider="openai")
    with pytest.raises(Exception, match="API Connection Error"):
        gen.generate_function_docs("my_func", ["a"], "int", "Original doc")

# TC-DI-01: Ensure no modification of source files
def test_no_source_modification(tmp_path):
    src_file = tmp_path / "source.py"
    content = "def hello(): pass"
    src_file.write_text(content)
    
    # Simulate a run that should only read
    parse_file(src_file)
    
    assert src_file.read_text() == content

# TC-LOC-01: Unicode support
def test_unicode_support(tmp_path):
    code_file = tmp_path / "unicode_test.py"
    # Python 3 allows many non-ASCII characters in identifiers, but not emojis
    code_file.write_text("# -*- coding: utf-8 -*-\n# 测试注释\ndef 测试函数():\n    \"\"\"✨ doc\"\"\"\n    pass", encoding="utf-8")
    
    module = parse_file(code_file)
    assert module.functions[0].name == "测试函数"
    assert module.functions[0].docstring == "✨ doc"
