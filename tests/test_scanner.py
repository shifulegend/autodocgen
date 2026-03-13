"""Tests for the file system scanner."""
from pathlib import Path
import tempfile
import os
from autodocgen.scanner import scan_directory


def test_scan_finds_python_files(tmp_path):
    """scan_directory should find .py files in subdirectories."""
    (tmp_path / "mod.py").write_text("# module")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "nested.py").write_text("# nested")
    files = scan_directory(tmp_path, exclude_dirs=set())
    names = {f.name for f in files}
    assert "mod.py" in names
    assert "nested.py" in names


def test_scan_excludes_exact_dir(tmp_path):
    """Exact directory names in exclude_dirs should be excluded."""
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / "hidden.py").write_text("")
    (tmp_path / "visible.py").write_text("")
    files = scan_directory(tmp_path, exclude_dirs={"venv"})
    names = {f.name for f in files}
    assert "visible.py" in names
    assert "hidden.py" not in names


def test_scan_excludes_glob_pattern(tmp_path):
    """Glob patterns like '*.egg-info' should be honoured."""
    egg = tmp_path / "mypackage.egg-info"
    egg.mkdir()
    (egg / "PKG-INFO.py").write_text("")
    (tmp_path / "real.py").write_text("")
    files = scan_directory(tmp_path, exclude_dirs={"*.egg-info"})
    names = {f.name for f in files}
    assert "real.py" in names
    assert "PKG-INFO.py" not in names


def test_scan_returns_empty_for_no_python_files(tmp_path):
    """Returns empty list when no .py files exist."""
    (tmp_path / "README.md").write_text("hello")
    files = scan_directory(tmp_path)
    assert files == []


def test_scan_current_repo():
    """Integration: scanning the actual repo root should find Python files."""
    repo_root = Path(__file__).parent.parent  # tests/ -> repo root
    py_files = scan_directory(repo_root, exclude_dirs={"venv", ".venv", "__pycache__", ".git"})
    assert len(py_files) > 0, "Should find at least one Python file in the repo"
