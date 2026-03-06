"""AST-based parser for Python source files to extract code structure and docstrings."""
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union


@dataclass
class CodeFunction:
    """Represents a function or method."""
    name: str
    args: List[str]  # list of argument names (positional only for MVP)
    returns: Optional[str] = None  # return type annotation as string (or None)
    docstring: Optional[str] = None
    is_method: bool = False
    line_no: int = 0


@dataclass
class CodeClass:
    """Represents a class definition."""
    name: str
    bases: List[str] = field(default_factory=list)  # base class names (as strings)
    docstring: Optional[str] = None
    methods: List[CodeFunction] = field(default_factory=list)
    line_no: int = 0


@dataclass
class CodeModule:
    """Represents a module."""
    path: Path
    name: str  # module name (dot-separated relative to a package root, but we'll use relative stem)
    docstring: Optional[str] = None
    functions: List[CodeFunction] = field(default_factory=list)
    classes: List[CodeClass] = field(default_factory=list)


def _get_docstring(node: ast.AST) -> Optional[str]:
    """Extract docstring from a node that may have one."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return None
    if not node.body:
        return None
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
        return first.value.value.strip()
    return None


def _function_args_str(args: ast.arguments) -> List[str]:
    """Extract a simple list of argument names from ast.arguments."""
    names = []
    # posonlyargs, args, vararg, kwonlyargs, kwarg
    for arg in args.posonlyargs:
        names.append(arg.arg)
    for arg in args.args:
        names.append(arg.arg)
    if args.vararg:
        names.append(f"*{args.vararg.arg}")
    for arg in args.kwonlyargs:
        names.append(arg.arg)
    if args.kwarg:
        names.append(f"**{args.kwarg.arg}")
    return names


def parse_file(path: Path, base_package: Optional[str] = None) -> CodeModule:
    """
    Parse a Python file and return a CodeModule.
    base_package: optional root package name to compute fully qualified module name.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:
        raise ValueError(f"Cannot read {path}: {e}")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        raise ValueError(f"Syntax error in {path}: {e}")

    # Determine module name: use stem (filename without .py)
    # If within a package (has __init__.py), the package name would be derived from directories.
    # For MVP, we just use the stem.
    module_name = path.stem

    module = CodeModule(path=path, name=module_name)
    module.docstring = _get_docstring(tree)

    # Walk top-level statements
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            func = CodeFunction(
                name=node.name,
                args=_function_args_str(node.args),
                returns=ast.unparse(node.returns) if node.returns else None,
                docstring=_get_docstring(node),
                is_method=False,
                line_no=node.lineno,
            )
            module.functions.append(func)
        elif isinstance(node, ast.ClassDef):
            cls = CodeClass(
                name=node.name,
                bases=[ast.unparse(base) for base in node.bases],
                docstring=_get_docstring(node),
                line_no=node.lineno,
            )
            # Parse methods inside class
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method = CodeFunction(
                        name=item.name,
                        args=_function_args_str(item.args),
                        returns=ast.unparse(item.returns) if item.returns else None,
                        docstring=_get_docstring(item),
                        is_method=True,
                        line_no=item.lineno,
                    )
                    cls.methods.append(method)
            module.classes.append(cls)
        # ignore imports, assignments, etc.

    return module