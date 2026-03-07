"""AST-based parser to extract code documentation structures."""
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class CodeFunction:
    name: str
    args: List[str]
    returns: Optional[str]
    docstring: Optional[str]
    lineno: int

@dataclass
class CodeClass:
    name: str
    bases: List[str]
    docstring: Optional[str]
    methods: List[CodeFunction] = field(default_factory=list)
    lineno: int

@dataclass
class CodeModule:
    filepath: Path
    module_name: str
    docstring: Optional[str]
    functions: List[CodeFunction] = field(default_factory=list)
    classes: List[CodeClass] = field(default_factory=list)


def _get_docstring(node: ast.AST) -> Optional[str]:
    node_doc = ast.get_docstring(node)
    return node_doc.strip() if node_doc else None


def _extract_function(node: ast.FunctionDef) -> CodeFunction:
    args = [arg.arg for arg in node.args.args]
    returns = None
    if node.returns:
        returns = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
    return CodeFunction(name=node.name, args=args, returns=returns, docstring=_get_docstring(node), lineno=node.lineno)


def _extract_class(node: ast.ClassDef) -> CodeClass:
    bases = []
    for base in node.bases:
        if hasattr(ast, 'unparse'):
            bases.append(ast.unparse(base))
        else:
            bases.append(str(base))
    methods = []
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            methods.append(_extract_function(item))
    return CodeClass(name=node.name, bases=bases, docstring=_get_docstring(node), methods=methods, lineno=node.lineno)


def parse_file(filepath: str | Path) -> CodeModule:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    source = path.read_text(encoding='utf-8')
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {filepath}: {e}")
    module_doc = _get_docstring(tree)
    module = CodeModule(filepath=path, module_name=path.stem, docstring=module_doc)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and not node.col_offset:
            module.functions.append(_extract_function(node))
        elif isinstance(node, ast.ClassDef) and not node.col_offset:
            module.classes.append(_extract_class(node))
    return module

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m autodocgen.parser <file.py>")
        sys.exit(1)
    mod = parse_file(sys.argv[1])
    print(f"Module: {mod.module_name}")
    if mod.docstring:
        print(f"Docstring: {mod.docstring[:80]}...")
    print(f"Functions: {len(mod.functions)}")
    for fn in mod.functions:
        print(f"  - {fn.name}({', '.join(fn.args)}) -> {fn.returns or 'None'}")
    print(f"Classes: {len(mod.classes)}")
    for cls in mod.classes:
        print(f"  - {cls.name} (bases: {', '.join(cls.bases)})")
        for meth in cls.methods:
            print(f"      * {meth.name}()")
