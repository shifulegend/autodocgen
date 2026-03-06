"""Run basic parser tests."""
from pathlib import Path
from autodocgen.parser import parse_file

def test_parse_parser_itself():
    parser_path = Path(__file__).parent.parent / 'autodocgen' / 'parser.py'
    if not parser_path.exists():
        parser_path = Path(__file__).parent.parent / 'parser.py'
    mod = parse_file(parser_path)
    assert mod.module_name in ('parser', 'autodocgen.parser')
    assert mod.docstring is not None
    assert len(mod.functions) >= 1
    assert len(mod.classes) >= 1
    print(f"Parsed {mod.filepath} with {len(mod.functions)} functions, {len(mod.classes)} classes")

if __name__ == "__main__":
    test_parse_parser_itself()
    print("All tests passed.")
