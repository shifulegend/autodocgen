"""File system scanner for Python source files."""
import fnmatch
from pathlib import Path


def scan_directory(root_path: str | Path, exclude_dirs=None) -> list[Path]:
    """Recursively find all .py files under root_path, excluding specified directories.

    Supports both exact directory names (e.g. 'venv') and glob patterns
    (e.g. '*.egg-info') in exclude_dirs.
    """
    if exclude_dirs is None:
        exclude_dirs = {
            'venv', '__pycache__', '.git', 'node_modules',
            'dist', 'build', '*.egg-info', 'docs', 'tests',
        }
    root = Path(root_path).resolve()
    py_files = []
    for path in root.rglob('*.py'):
        parts = path.parts
        excluded = False
        for part in parts:
            for pattern in exclude_dirs:
                if fnmatch.fnmatch(part, pattern):
                    excluded = True
                    break
            if excluded:
                break
        if not excluded:
            py_files.append(path)
    return py_files

if __name__ == "__main__":
    files = scan_directory('.')
    for f in files[:10]:
        print(f)
    print(f"Total: {len(files)} files")
