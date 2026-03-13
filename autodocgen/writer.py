"""Write generated documentation to Markdown files using Jinja2 templates."""
from pathlib import Path
from typing import List, Set, Optional
from autodocgen.parser import CodeModule, CodeClass, CodeFunction
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Initialize Jinja2 environment
template_dir = Path(__file__).parent / "templates"
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

def render_module_doc(module: CodeModule, class_docs: dict, function_docs: dict, all_module_names: Set[str] = None) -> str:
    """
    Render the module-level documentation Markdown using a template.
    """
    try:
        template = env.get_template("module.md.j2")
    except Exception:
        # Fallback if template missing (though it shouldn't be)
        return f"# Module: {module.module_name}\n\n_Template error. Documentation could not be rendered._"
    
    related = []
    if all_module_names and module.imports:
        for imp in module.imports:
            candidate = imp.split('.')[-1]
            if candidate in all_module_names and candidate != module.module_name:
                related.append(candidate)
    
    return template.render(
        module=module,
        class_docs=class_docs,
        function_docs=function_docs,
        related_modules=sorted(set(related))
    )

def write_module_doc(module: CodeModule, output_dir: Path, class_docs: dict, function_docs: dict, all_module_names: Set[str] = None):
    """Write module documentation to a Markdown file under output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    content = render_module_doc(module, class_docs, function_docs, all_module_names)
    out_file = output_dir / f"{module.module_name}.md"
    out_file.write_text(content, encoding="utf-8")
    return out_file

def write_index(modules: List[CodeModule], output_dir: Path, project_name: str = "Project"):
    """Generate an index.md file listing all modules, classes, and functions with links."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        template = env.get_template("index.md.j2")
        content = template.render(modules=modules, project_name=project_name)
    except Exception:
         content = f"# {project_name} Documentation\n\n_Index template error._"
    
    index_file = output_dir / "index.md"
    index_file.write_text(content, encoding="utf-8")
    return index_file
