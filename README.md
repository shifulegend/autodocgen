# AutoDocGen

> AI-powered Markdown documentation generator for Python projects.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

AutoDocGen scans your Python source code, extracts docstrings and structure using Python's built-in AST parser, and uses AI to generate comprehensive, readable Markdown documentation — one file per module plus a navigable index.

---

## Features

- **Multi-Provider Support** — Works with **OpenRouter**, **Groq**, **Google Gemini**, and **OpenAI**.
- **AST-based parsing** — No fragile regex. Uses Python's `ast` module to accurately extract modules, classes, methods, and functions.
- **Jinja2 Templates** — Clean, customizable Markdown output using industry-standard templates.
- **Async function support** — Correctly identifies and labels `async def` functions.
- **Cross-module linking** — Automatically traces imports to create related module links.
- **Navigable index** — Produces a comprehensive `index.md`.
- **Flexible configuration** — Supports `.env`, `autodocgen.yaml`, `pyproject.toml`, and CLI flags.

---

## Installation

```bash
git clone https://github.com/shifulegend/autochamp-autodocgen-1
cd autochamp-autodocgen-1
pip install .
```

---

## Configuration

Set your API keys in a `.env` file (which is gitignored):

```env
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...
GOOGLE_API_KEY=AIza...
```

### `autodocgen.yaml` example

```yaml
llm:
  provider: groq
  model: llama-3.1-8b-instant

output:
  dir: docs

source:
  - autodocgen
```

---

## Usage

```bash
# Generate docs using settings from autodocgen.yaml
autodocgen . --verbose

# Override provider/model via CLI
autodocgen . --output docs_custom -v
```

---

## Roadmap

- [x] Multi-provider LLM support (OpenRouter, Groq, Gemini)
- [x] Jinja2 template-based rendering
- [ ] Async AI calls for faster generation
- [ ] Incremental generation (skip unchanged files)
- [ ] HTML and reStructuredText output formats

---

## License

[MIT](LICENSE) — Copyright (c) 2025-2026 AutoDocGen Team
