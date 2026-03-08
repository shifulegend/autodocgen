"""End-to-end integration tests for autodocgen."""
import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from click.testing import CliRunner
from autodocgen.cli import main
from autodocgen.generator import AIDocGenerator
from autodocgen.parser import CodeModule, CodeClass, CodeFunction


@pytest.fixture
def sample_project(tmp_path):
    """Create a small sample Python project."""
    src_dir = tmp_path / "sample"
    src_dir.mkdir()
    # Create a module with class and function
    (src_dir / "mymath.py").write_text("""
\"\"\"Simple math operations.\"\"\"

def add(a, b):
    \"\"\"Add two numbers and return the sum.\"\"\"
    return a + b

class Calculator:
    \"\"\"A basic calculator.\"\"\"

    def multiply(self, x, y):
        \"\"\"Multiply two numbers.\"\"\"
        return x * y
""")
    # Create another module that imports from mymath
    (src_dir / "app.py").write_text("""
\"\"\"Main application.\"\"\"
from mymath import add, Calculator

def main():
    result = add(2, 3)
    calc = Calculator()
    return result, calc.multiply(4, 5)
""")
    return src_dir


def mock_ai_responses():
    """Return AI-generated documentation strings."""
    return {
        "function": "**Add Function**\n\nAdds two numbers together.\n\n**Parameters:**\n- a (int): First number\n- b (int): Second number\n\n**Returns:** int: The sum",
        "class": "**Calculator Class**\n\nA basic calculator for arithmetic operations.\n\n**Methods:**\n- multiply(x, y): Multiply two numbers",
        "module": "**{name} Module**\n\nProvides {desc}.",
    }


def test_end_to_end_with_mocked_ai(sample_project, tmp_path, monkeypatch):
    """Test full pipeline: parse, generate, write with mocked AI."""
    output_dir = tmp_path / "docs"

    # Pre-create output directory to avoid race conditions
    output_dir.mkdir(parents=True, exist_ok=True)

    responses = mock_ai_responses()
    call_log = []

    def mock_generate_function_docs(self, func_name, args, returns, existing_doc):
        call_log.append(("function", func_name))
        return responses["function"]

    def mock_generate_class_docs(self, class_name, bases, methods, existing_doc):
        call_log.append(("class", class_name))
        return responses["class"]

    # Apply mocks (note: generate_module_docs is not called in current implementation)
    monkeypatch.setattr(AIDocGenerator, "generate_function_docs", mock_generate_function_docs)
    monkeypatch.setattr(AIDocGenerator, "generate_class_docs", mock_generate_class_docs)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    # Run CLI
    runner = CliRunner()
    result = runner.invoke(main, [
        str(sample_project),
        "--output", str(output_dir),
    ], catch_exceptions=False)

    assert result.exit_code == 0, f"CLI failed: {result.output}"
    assert "Documentation generated in" in result.output

    # Check output files exist
    assert (output_dir / "mymath.md").exists()
    assert (output_dir / "app.md").exists()
    assert (output_dir / "index.md").exists()

    # Check content contains mock AI docs
    mymath_content = (output_dir / "mymath.md").read_text()
    assert "Add Function" in mymath_content or "Adds two numbers" in mymath_content
    assert "Calculator Class" in mymath_content or "calculator" in mymath_content

    # Check index
    index_content = (output_dir / "index.md").read_text()
    assert "mymath" in index_content
    assert "app" in index_content

    # Verify AI calls: expect class and function docs generation
    assert ("function", "add") in call_log
    assert ("class", "Calculator") in call_log
    assert ("function", "main") in call_log  # from app.py


def test_cli_missing_api_key(sample_project, tmp_path, monkeypatch):
    """Test CLI exits with error when API key is missing."""
    output_dir = tmp_path / "docs"
    # Ensure no API key in env
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runner = CliRunner()
    result = runner.invoke(main, [
        str(sample_project),
        "--output", str(output_dir)
    ], catch_exceptions=False)
    assert result.exit_code == 1
    output = result.output.lower()
    assert "api key" in output or "configuration error" in output


def test_cli_no_python_files(tmp_path, monkeypatch):
    """Test CLI when source directory has no Python files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    output_dir = tmp_path / "docs"
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    runner = CliRunner()
    result = runner.invoke(main, [
        str(empty_dir),
        "--output", str(output_dir)
    ], catch_exceptions=False)
    assert result.exit_code == 1
    assert "No Python files found" in result.output

