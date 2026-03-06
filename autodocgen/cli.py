"""CLI entry point for AutoDocGen."""
import sys
from pathlib import Path
import click
from .config import Config
from .scanner import scan_directory
from .parser import parse_file, CodeModule
from .generator import AIDocGenerator
from .writer import write_module_doc


@click.command()
@click.argument("source", default=".")
@click.option("--output", "-o", default="docs", help="Output directory for generated docs.")
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file.")
@click.option("--verbose", "-v", is_flag=True, help="Verbose logging.")
def main(source: str, output: str, config: str, verbose: bool):
    """Generate AI-powered documentation for Python code."""
    try:
        cfg = Config.load(config_path=Path(config) if config else None, overrides={"output": {"dir": output}, "source": source})
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"Config: API key present={bool(cfg.openai_api_key)}, model={cfg.openai_model}, output={cfg.output_dir}")

    # Resolve source paths
    src_paths = [Path(p) for p in cfg.source_paths]
    all_py_files = []
    for src in src_paths:
        if src.is_dir():
            files = scan_directory(src, exclude_patterns=cfg.exclude_patterns)
            all_py_files.extend(files)
        elif src.is_file() and src.suffix == ".py":
            all_py_files.append(src)
        else:
            click.echo(f"Warning: skipping {src} (not a directory or .py file)", err=True)

    if not all_py_files:
        click.echo("No Python files found to document.", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"Found {len(all_py_files)} Python files to process.")

    # Initialize AI generator
    ai_gen = AIDocGenerator(api_key=cfg.openai_api_key, model=cfg.openai_model)

    # For MVP, we'll process each file as an independent module, generate docs for its contents
    output_dir = Path(cfg.output_dir)
    total_errors = 0

    for py_file in all_py_files:
        try:
            if verbose:
                click.echo(f"Parsing {py_file}...")
            module: CodeModule = parse_file(py_file)
        except Exception as e:
            click.echo(f"Error parsing {py_file}: {e}", err=True)
            total_errors += 1
            continue

        # Generate docs for each class and function
        class_docs = {}
        function_docs = {}
        # Generate class docs first (including methods)
        for cls in module.classes:
            try:
                if verbose:
                    click.echo(f"  Generating docs for class {cls.name}...")
                doc = ai_gen.generate_class_docs(
                    class_name=cls.name,
                    bases=cls.bases,
                    methods=cls.methods,
                    existing_doc=cls.docstring,
                )
                class_docs[cls.name] = doc
            except Exception as e:
                if verbose:
                    click.echo(f"    Error: {e}", err=True)
                class_docs[cls.name] = f"*Error generating documentation: {e}*"

        # Generate function docs
        for fn in module.functions:
            try:
                if verbose:
                    click.echo(f"  Generating docs for function {fn.name}...")
                doc = ai_gen.generate_function_docs(
                    func_name=fn.name,
                    args=fn.args,
                    returns=fn.returns,
                    existing_doc=fn.docstring,
                )
                function_docs[fn.name] = doc
            except Exception as e:
                if verbose:
                    click.echo(f"    Error: {e}", err=True)
                function_docs[fn.name] = f"*Error generating documentation: {e}*"

        # Write module documentation
        try:
            out_file = write_module_doc(module, output_dir, class_docs, function_docs)
            if verbose:
                click.echo(f"  Wrote {out_file}")
        except Exception as e:
            click.echo(f"Error writing docs for {py_file}: {e}", err=True)
            total_errors += 1

    click.echo(f"Documentation generated in {output_dir.absolute()}.")
    if total_errors:
        click.echo(f"Completed with {total_errors} errors.", err=True)
        sys.exit(1)
    else:
        click.echo("Done.")


if __name__ == "__main__":
    main()