"""Write generated documentation to Markdown files."""
from pathlib import Path
from typing import List, Set
from dataclasses import dataclass
from autodocgen.parser import CodeModule, CodeClass, CodeFunction
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_module_doc(module: CodeModule, class_docs: dict, function_docs: dict, all_module_names: Set[str] = None) -> str:
    """
    Render the module-level documentation Markdown.
    This combines module overview, classes, and functions.
    Optionally includes cross-links to related modules based on imports.
    """
    # For MVP, we'll assemble manually without templates.
    lines = []
    lines.append(f"# Module: {module.module_name}\n")
    if module.docstring:
        lines.append(f"{module.docstring}\n")
    else:
        lines.append("_No module docstring provided._\n")

    if module.classes:
        lines.append("## Classes\n")
        for cls in module.classes:
            lines.append(f"### {cls.name}\n")
            if cls.docstring:
                lines.append(f"{cls.docstring}\n")
            # Insert AI-generated class docs if available
            if cls.name in class_docs:
                lines.append(class_docs[cls.name])
                lines.append("")
            else:
                lines.append("_Documentation pending._\n")
            # List methods
            if cls.methods:
                lines.append("**Methods:**\n")
                for meth in cls.methods:
                    sig = f"`{meth.name}({', '.join(meth.args)})`"
                    lines.append(f"- {sig}")
                    if meth.docstring:
                        lines.append(f"  - {meth.docstring}")
                    else:
                        lines.append("  - _No docstring_")
                lines.append("")

    if module.functions:
        lines.append("## Functions\n")
        for fn in module.functions:
            lines.append(f"### {fn.name}\n")
            sig = f"`{fn.name}({', '.join(fn.args)})`"
            if fn.returns:
                sig += f" -> `{fn.returns}`"
            lines.append(f"{sig}\n")
            if fn.docstring:
                lines.append(f"{fn.docstring}\n")
            # AI-generated
            if fn.name in function_docs:
                lines.append(function_docs[fn.name])
                lines.append("")
            else:
                lines.append("_Documentation pending._\n")

    # Add cross-links to related modules based on imports
    if all_module_names and module.imports:
        related = []
        for imp in module.imports:
            # Extract the final component of import path
            candidate = imp.split('.')[-1]
            if candidate in all_module_names and candidate != module.module_name:
                related.append(candidate)
        if related:
            lines.append("## Related Modules\n")
            for name in sorted(set(related)):
                lines.append(f"- [{name}]({name}.md)")
            lines.append("")

    return "\n".join(lines)


def write_module_doc(module: CodeModule, output_dir: Path, class_docs: dict, function_docs: dict, all_module_names: Set[str] = None):
    """Write module documentation to a Markdown file under output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    content = render_module_doc(module, class_docs, function_docs, all_module_names)
    out_file = output_dir / f"{module.module_name}.md"
    out_file.write_text(content, encoding="utf-8")
    return out_file


def write_index(modules: List[CodeModule], output_dir: Path):
    """Generate an index.md file listing all modules, classes, and functions with links."""
    output_dir = Path(output_dir)
    lines = ["# AutoDocGen Documentation\n", "## Index\n", "This index provides quick navigation to all documented code elements.\n"]

    # Group by module
    for module in modules:
        lines.append(f"### Module: {module.module_name}\n")
        lines.append(f"- **Module page**: [{module.module_name}.md]({module.module_name}.md)\n")

        if module.classes:
            lines.append("**Classes:**\n")
            for cls in module.classes:
                anchor = cls.name.lower()
                lines.append(f"  - [{cls.name}]({module.module_name}.md#{anchor})\n")
        if module.functions:
            lines.append("**Functions:**\n")
            for fn in module.functions:
                anchor = fn.name.lower()
                lines.append(f"  - [{fn.name}]({module.module_name}.md#{anchor})\n")
        lines.append("")  # blank line

    content = "\n".join(lines)
    index_file = output_dir / "index.md"
    index_file.write_text(content, encoding="utf-8")
    return index_file