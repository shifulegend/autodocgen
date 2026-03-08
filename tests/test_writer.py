"""Tests for the writer module."""
import tempfile
from pathlib import Path
from autodocgen.writer import render_module_doc, write_module_doc, write_index
from autodocgen.parser import CodeModule, CodeClass, CodeFunction


def test_render_module_doc_basic():
    """Test rendering a module with a class and function."""
    module = CodeModule(
        filepath=Path("test.py"),
        module_name="mymodule",
        docstring="A test module",
        classes=[
            CodeClass(
                name="MyClass",
                bases=[],
                docstring="A test class",
                lineno=1,
                methods=[
                    CodeFunction(name="method1", args=["self", "x"], returns=None, docstring="Does something", lineno=2)
                ]
            )
        ],
        functions=[
            CodeFunction(name="my_func", args=["a", "b"], returns="str", docstring="A test function", lineno=10)
        ],
        imports=[]
    )
    class_docs = {"MyClass": "AI-generated class documentation."}
    function_docs = {"my_func": "AI-generated function documentation."}

    content = render_module_doc(module, class_docs, function_docs, set())

    # Check structure
    assert "# Module: mymodule" in content
    assert "A test module" in content
    assert "## Classes" in content
    assert "## Functions" in content
    assert "### MyClass" in content
    assert "AI-generated class documentation" in content
    assert "### my_func" in content
    assert "AI-generated function documentation" in content
    assert "`my_func(a, b)`" in content


def test_render_module_doc_with_crosslinks():
    """Test that cross-links to related modules are generated."""
    module = CodeModule(
        filepath=Path("test.py"),
        module_name="consumer",
        docstring="Consumes other modules",
        classes=[],
        functions=[],
        imports=["othermodule", "thirdmodule.submod"]
    )
    all_modules = {"othermodule", "thirdmodule", "somemodule"}

    content = render_module_doc(module, {}, {}, all_modules)

    assert "## Related Modules" in content
    assert "- [othermodule](othermodule.md)" in content
    # thirdmodule's final component is 'submod', not 'thirdmodule', so no link
    assert "thirdmodule" not in content.lower() or "submod" in content
    assert "somemodule" not in content  # not imported


def test_render_module_doc_no_docstring():
    """Test module with no docstring shows placeholder."""
    module = CodeModule(
        filepath=Path("test.py"),
        module_name="empty",
        docstring=None,
        classes=[],
        functions=[],
        imports=[]
    )
    content = render_module_doc(module, {}, {}, set())
    assert "_No module docstring provided._" in content


def test_render_module_doc_missing_ai_docs():
    """Test missing AI-generated docs show placeholder."""
    module = CodeModule(
        filepath=Path("test.py"),
        module_name="partial",
        docstring="Has some docs",
        classes=[
            CodeClass(name="PartialClass", bases=[], docstring="Class doc", lineno=1, methods=[])
        ],
        functions=[
            CodeFunction(name="partial_func", args=[], returns=None, docstring="Func doc", lineno=5)
        ],
        imports=[]
    )
    # Empty class_docs and function_docs
    content = render_module_doc(module, {}, {}, set())
    assert "_Documentation pending._" in content


def test_write_module_doc_creates_file(tmp_path):
    """Test write_module_doc creates file in output directory."""
    module = CodeModule(
        filepath=Path("test.py"),
        module_name="testmod",
        docstring="Test",
        classes=[],
        functions=[],
        imports=[]
    )
    out_dir = tmp_path / "docs"
    out_file = write_module_doc(module, out_dir, {}, {}, set())
    assert out_file.exists()
    content = out_file.read_text()
    assert "# Module: testmod" in content


def test_write_index_generates_correct_links(tmp_path):
    """Test index file generation with modules, classes, functions."""
    modules = [
        CodeModule(
            filepath=Path("a.py"),
            module_name="moda",
            docstring="",
            classes=[CodeClass(name="ClassA", bases=[], docstring="", lineno=1, methods=[])],
            functions=[CodeFunction(name="func_a", args=[], returns=None, docstring="", lineno=10)],
            imports=[]
        ),
        CodeModule(
            filepath=Path("b.py"),
            module_name="modb",
            docstring="",
            classes=[],
            functions=[CodeFunction(name="func_b", args=[], returns=None, docstring="", lineno=5)],
            imports=[]
        )
    ]
    out_dir = tmp_path / "docs"
    index_file = write_index(modules, out_dir)
    assert index_file.exists()
    content = index_file.read_text()
    assert "### Module: moda" in content
    assert "[moda.md](moda.md)" in content
    assert "ClassA" in content
    assert "func_a" in content
    assert "modb" in content
    assert "func_b" in content
