"""Tests for the generator module with OpenAI API mocking."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from autodocgen.generator import AIDocGenerator
from autodocgen.parser import CodeClass, CodeFunction


def mock_openai_response(content="Generated documentation"):
    """Create a mock OpenAI response object."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.fixture
def generator():
    """Create an AIDocGenerator with a dummy API key."""
    return AIDocGenerator(api_key="test-key", model="gpt-4o")


def test_generate_module_docs(generator):
    """Test module documentation generation."""
    with patch.object(generator.client.chat.completions, 'create', return_value=mock_openai_response("Module docs")):
        result = generator.generate_module_docs(
            module_name="testmod",
            classes=[CodeClass(name="MyClass", bases=[], docstring="", lineno=1, methods=[])],
            functions=[CodeFunction(name="my_func", args=[], returns=None, docstring="", lineno=5)],
            existing_doc="A test module"
        )
    assert result == "Module docs"


def test_generate_class_docs(generator):
    """Test class documentation generation."""
    with patch.object(generator.client.chat.completions, 'create', return_value=mock_openai_response("Class docs")):
        result = generator.generate_class_docs(
            class_name="MyClass",
            bases=["BaseClass"],
            methods=[CodeFunction(name="method1", args=[], returns=None, docstring="", lineno=2)],
            existing_doc="A test class"
        )
    assert result == "Class docs"


def test_generate_function_docs(generator):
    """Test function documentation generation."""
    with patch.object(generator.client.chat.completions, 'create', return_value=mock_openai_response("Function docs")):
        result = generator.generate_function_docs(
            func_name="my_func",
            args=["x", "y"],
            returns="str",
            existing_doc="A test function"
        )
    assert result == "Function docs"


def test_ai_error_handling(generator):
    """Test that OpenAI API errors return fallback message."""
    with patch.object(generator.client.chat.completions, 'create', side_effect=Exception("API error")):
        result = generator.generate_function_docs(
            func_name="test",
            args=[],
            returns=None,
            existing_doc=None
        )
    assert "Error generating documentation" in result
    assert "API error" in result


def test_prompt_content_includes_signature():
    """Verify that prompts include necessary information."""
    generator = AIDocGenerator(api_key="test")
    # Mock to capture the prompt
    with patch.object(generator.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = mock_openai_response("Result")
        generator.generate_function_docs(
            func_name="add",
            args=["a", "b"],
            returns="int",
            existing_doc="Adds two numbers"
        )
        # Check that the prompt was constructed properly
        call_args = mock_create.call_args
        messages = call_args.kwargs['messages']
        user_message = messages[1]['content']
        assert "Signature: add(a, b) -> int" in user_message
        assert "Existing docstring: Adds two numbers" in user_message
        assert "Parameter descriptions" in user_message
        assert "Return value description" in user_message


def test_module_prompt_includes_imports():
    """Verify module prompt includes class and function names."""
    generator = AIDocGenerator(api_key="test")
    with patch.object(generator.client.chat.completions, 'create', return_value=mock_openai_response()) as mock_create:
        generator.generate_module_docs(
            module_name="mymod",
            classes=[CodeClass(name="ClassA", bases=[], docstring="", lineno=1, methods=[]), CodeClass(name="ClassB", bases=[], docstring="", lineno=5, methods=[])],
            functions=[CodeFunction(name="func1", args=[], returns=None, docstring="", lineno=10), CodeFunction(name="func2", args=[], returns=None, docstring="", lineno=20)],
            existing_doc="Module doc"
        )
        messages = mock_create.call_args.kwargs['messages']
        user_message = messages[1]['content']
        assert "Module name: mymod" in user_message
        assert "ClassA" in user_message and "ClassB" in user_message
        assert "func1" in user_message and "func2" in user_message

