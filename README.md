# AutoDocGen

> AI-powered Markdown documentation generator for Python projects.

[![CI](https://github.com/shifulegend/autochamp-autodocgen-1/actions/workflows/ci.yml/badge.svg)](https://github.com/shifulegend/autochamp-autodocgen-1/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/autodocgen.svg)](https://badge.fury.io/py/autodocgen)

AutoDocGen scans your Python source code, extracts docstrings and structure using Python's built-in AST parser, and uses OpenAI to generate comprehensive, readable Markdown documentation — one file per module plus a navigable index.

---

## Features

- **AST-based parsing** — No fragile regex. Uses Python's own `ast` module to accurately extract modules, classes (including inheritance), methods, functions, and type annotations.
- **AI-expanded documentation** — Sends each code element's signature and existing docstring to OpenAI and gets back structured, readable Markdown.
- **Async function support** — Correctly identifies and labels `async def` functions and methods.
- **Cross-module linking** — Automatically generates `## Related Modules` sections by tracing import statements.
- **Navigable index** — Produces an `index.md` with links to every module, class, and function.
- **Flexible configuration** — Configure via `pyproject.toml`, `autodocgen.yaml`, environment variables, or CLI flags.
- **Glob-aware exclusions** — Exclude directories by exact name or glob pattern (e.g. `*.egg-info`).

---

## Installation

```bash
pip install autodocgen
```

> **Note:** An [OpenAI API key](https://platform.openai.com/api-keys) is required. Set it as an environment variable before running:
> ```bash
> export OPENAI_API_KEY="sk-..."
> ```

---

## Quick Start

```bash
# Generate docs for your project into ./docs/
autodocgen path/to/your/project --output docs/

# Verbose output to see what is being processed
autodocgen . --output docs/ --verbose

# Use a custom config file
autodocgen . --config autodocgen.yaml
```

**Example output structure:**

```
docs/
├── index.md          ← links to all modules, classes, functions
├── scanner.md
├── parser.md
├── generator.md
└── config.md
```

---

## Configuration

AutoDocGen reads configuration in the following priority order (highest wins):

1. Command-line flags (`--output`, `--config`)
2. `OPENAI_API_KEY` environment variable
3. Explicit `--config path/to/autodocgen.yaml`
4. `autodocgen.yaml` auto-discovered in the current directory
5. `[tool.autodocgen]` section in `pyproject.toml`

### `autodocgen.yaml` example

```yaml
openai:
  api_key: ${OPENAI_API_KEY}   # always use an environment variable for secrets
  model: gpt-4o
output:
  dir: docs
source: src
exclude:
  - venv
  - .venv
  - __pycache__
  - "*.egg-info"
```

### `pyproject.toml` example

```toml
[tool.autodocgen]
source = "src"

[tool.autodocgen.openai]
model = "gpt-4o"

[tool.autodocgen.output]
dir = "docs"
```

---

## How It Works

1. **Scan** — Recursively finds all `.py` files, respecting exclusion patterns.
2. **Parse** — Uses Python's `ast` module to extract the structure of every module: classes, async/sync functions, arguments, return types, and docstrings.
3. **Generate** — Sends each element's signature and docstring to OpenAI with a focused prompt; receives back structured Markdown prose.
4. **Write** — Assembles and writes one `.md` file per module and a top-level `index.md`.

---

## Development

```bash
# Clone and install in editable mode
git clone https://github.com/shifulegend/autochamp-autodocgen-1
cd autochamp-autodocgen-1
pip install -e .[dev]

# Run the full test suite
pytest

# Run with coverage
pytest --cov=autodocgen --cov-report=term-missing
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on pull requests, code style, and the development workflow.

---

## Roadmap

- [ ] Async OpenAI calls for faster parallel generation
- [ ] Support for additional LLM providers (Anthropic Claude, local Ollama models)
- [ ] Module-level constant and type alias extraction
- [ ] HTML and reStructuredText output formats
- [ ] Incremental generation (skip unchanged files)

---

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 Nitika Saraogi
