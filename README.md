# AutoDocGen

> AI-powered documentation generator for Python code.

AutoDocGen is a command-line tool that scans your Python source code, extracts docstrings and comments, and uses AI to generate comprehensive Markdown documentation.

## Installation

```bash
pip install autodocgen
```

## Usage

```bash
# Generate docs for a project
autodocgen path/to/your/project --output docs/

# With custom config
autodocgen . --config autodocgen.yaml
```

## Configuration

AutoDocGen reads configuration from `pyproject.toml` or `autodocgen.yaml`:

```yaml
openai:
  api_key: ${OPENAI_API_KEY}  # recommended: use environment variable
  model: gpt-4o
output:
  dir: docs
```

## How It Works

1. **Scan**: Recursively finds all `.py` files (excluding virtualenvs, tests, etc.)
2. **Parse**: Uses Python's AST to extract modules, classes, functions, and their docstrings.
3. **Generate**: Sends each code element to the AI with a prompt to expand docstrings into full documentation.
4. **Write**: Renders Markdown files using Jinja2 templates, organized by module hierarchy.

## Development

```bash
# Clone and install in editable mode
git clone https://github.com/yourusername/autochamp-autodocgen-1
cd autodocgen
pip install -e .[dev]

# Run tests
pytest tests/
```

## License

MIT