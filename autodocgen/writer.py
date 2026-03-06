"""Write generated documentation to Markdown files."""
from pathlib import Path
from typing import List
from dataclasses import dataclass
from autodocgen.parser import CodeModule, CodeClass, CodeFunction
from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_module_doc(module: CodeModule, class_docs: dict, function_docs: dict) -> str:
    """
    Render the module-level documentation Markdown.
    This combines module overview, classes, and functions.
    """
    # For MVP, we'll assemble manually without templates.
    lines = []
    lines.append(f"# Module: {module.name}\n")
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

    return "\n".join(lines)


def write_module_doc(module: CodeModule, output_dir: Path, class_docs: dict, function_docs: dict):
    """Write module documentation to a Markdown file under output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    content = render_module_doc(module, class_docs, function_docs)
    out_file = output_dir / f"{module.name}.md"
    out_file.write_text(content, encoding="utf-8")
    return out_file