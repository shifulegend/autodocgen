"""Placeholder scanner tests."""
from pathlib import Path
from autodocgen.scanner import scan_directory

def test_scan_current_repo():
    repo_root = Path(__file__).parent.parent.parent
    py_files = scan_directory(repo_root)
    assert len(py_files) > 0
    print(f"Found {len(py_files)} Python files in repo root")

if __name__ == "__main__":
    test_scan_current_repo()
    print("Scanner test passed.")
