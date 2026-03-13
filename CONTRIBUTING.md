# Contributing to AutoDocGen

Thank you for your interest in contributing! This document explains how to get started.

---

## Development Setup

```bash
git clone https://github.com/shifulegend/autodocgen
cd autodocgen
pip install -e .[dev]
```

Run the full test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=autodocgen --cov-report=term-missing
```

---

## How to Submit a Pull Request

1. Fork the repository and create a branch from `main`.
2. Write your changes with clear commit messages.
3. Ensure all existing tests pass and add new tests for your changes.
4. Open a pull request targeting the `main` branch.
5. Fill in the PR template with a clear description of what changed and why.

---

## Publishing to PyPI (Maintainers Only)

AutoDocGen uses **OIDC Trusted Publisher** authentication — no API tokens are stored as GitHub secrets. This is the safest way to publish to PyPI.

### One-time setup (per environment)

**For TestPyPI:**
1. Go to [test.pypi.org/manage/account/publishing](https://test.pypi.org/manage/account/publishing/)
2. Click **"Add a new pending publisher"**
3. Fill in:
   - PyPI project name: `pypiautodocgen`
   - GitHub owner: `shifulegend`
   - Repository: `autodocgen`
   - Workflow filename: `release.yml`
   - Environment name: `testpypi`
4. Save.

**For real PyPI:**
1. Create an account at [pypi.org](https://pypi.org)
2. Go to [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing/)
3. Fill in the same fields as above, but use environment name `pypi`.
4. Save.

**In GitHub:**
- Go to the repository → **Settings → Environments**.
- Create two environments named exactly `testpypi` and `pypi`.
- No secrets needed — OIDC handles authentication automatically.

### Publishing a new release

```bash
# Update the version in pyproject.toml, then:
git tag v0.1.1
git push origin v0.1.1
```

The `release.yml` workflow will automatically run tests, build the package, and publish to both TestPyPI and PyPI.

---

## Code Style

- Python 3.10+ syntax throughout.
- No unused imports.
- All public functions should have docstrings.
- Prefer explicit error propagation over swallowing exceptions.

---

## Reporting Bugs

Please use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) when opening an issue.
