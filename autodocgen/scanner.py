"""File system scanner for Python source files."""
from pathlib import Path

def scan_directory(root_path: str | Path, exclude_dirs=None) -> list[Path]:
    if exclude_dirs is None:
        exclude_dirs = {'venv', '__pycache__', '.git', 'node_modules', 'dist', 'build', '*.egg-info', 'docs', 'tests'}
    root = Path(root_path).resolve()
    py_files = []
    for path in root.rglob('*.py'):
        if any(part in exclude_dirs for part in path.parts):
            continue
        py_files.append(path)
    return py_files

if __name__ == "__main__":
    files = scan_directory('.')
    for f in files[:10]:
        print(f)
    print(f"Total: {len(files)} files")
