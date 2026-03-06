"""File system scanner to discover Python source files."""
from pathlib import Path
from typing import Iterable, List


def scan_directory(
    root: Path,
    exclude_patterns: List[str] = None,
) -> List[Path]:
    """
    Recursively scan `root` for Python files, excluding directories matching patterns.
    Returns a list of absolute paths sorted alphabetically.
    """
    if exclude_patterns is None:
        exclude_patterns = ["venv", ".venv", "__pycache__", ".git", "node_modules", "dist", "build"]

    root = root.resolve()
    python_files: List[Path] = []

    for path in root.rglob("*.py"):
        # Check if any parent directory matches exclude patterns
        relative = path.relative_to(root)
        parts = relative.parts
        if any(part in exclude_patterns for part in parts):
            continue
        python_files.append(path)

    python_files.sort()
    return python_files