# Changelog

All notable changes to AutoDocGen are documented here.

## [Unreleased]

### Planned for v0.2.0
- Async OpenAI API calls for parallel, faster documentation generation
- Abstract LLM provider interface (support for Anthropic Claude, Ollama local models)
- Module-level constant and type alias extraction (`ast.AnnAssign`)
- HTML and reStructuredText output formats

---

## [0.1.0] — 2026-03-10

### Added
- AST-based Python code parser (`parser.py`) — extracts modules, classes, async/sync functions, arguments, return types, and docstrings
- File system scanner (`scanner.py`) with glob-pattern-aware directory exclusions
- OpenAI-powered documentation generator (`generator.py`) with configurable `max_tokens`
- Markdown writer (`writer.py`) — per-module pages with cross-links and a navigable index
- CLI entry point (`autodocgen`) built with Click
- Configuration loading from `pyproject.toml`, `autodocgen.yaml`, environment variables, and CLI flags
- GitHub Actions CI workflow testing Python 3.10, 3.11, and 3.12
- GitHub Actions release workflow (tag-triggered, publishes to TestPyPI and PyPI via OIDC)
- Comprehensive test suite including parser, scanner, config, writer, generator, and large multi-file integration tests

### Fixed
- Dead code in relative import handling (`parser.py`)
- `ast.walk` replaced with `tree.body` iteration for correct top-level node extraction
- `*.egg-info` glob pattern in scanner now correctly excluded via `fnmatch`
- Silent swallowing of malformed `pyproject.toml` errors in config replaced with a `warnings.warn`
- `autodocgen.yaml` auto-discovery implemented (was documented but not coded)
- AI generation errors now propagate to the CLI and increment the error counter
- Unused Jinja2 imports removed from `writer.py`
- Hardcoded "AutoDocGen Documentation" index title replaced with configurable `project_name`
- Release workflow changed from push-to-main trigger to version-tag trigger

### Changed
- `toml` dependency replaced with stdlib `tomllib` (Python 3.11+) or `tomli` backport (Python 3.10)
- Copyright holder updated to Nitika Saraogi
