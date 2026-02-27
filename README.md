# docgen — Automated Python Docstring Generator, Validator & Coverage Suite

[![CI](https://github.com/your-org/docgen/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/docgen/actions)
[![PyPI](https://img.shields.io/pypi/v/docgen.svg)](https://pypi.org/project/docgen/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-grade toolchain for **automatically generating docstrings**, **validating PEP 257 compliance**, and **enforcing documentation coverage** across your Python codebase.

---

## Features

| Feature | Description |
|---|---|
| 🔍 **AST Analysis** | Extracts functions, classes, methods, params, returns, decorators |
| ✍️ **4 Docstring Styles** | Google, NumPy, reStructuredText, PEP 257 |
| 📊 **Coverage Reports** | Per-file & project-wide coverage with JSON export |
| ✅ **PEP 257 Validation** | Powered by `pydocstyle` with configurable ignore rules |
| 🖥️ **Streamlit UI** | Interactive dashboard with filters, search, tooltips |
| ⚡ **CLI** | Full-featured `docgen` command |
| 📦 **Pip Library** | Import and use programmatically |
| 🔒 **Pre-commit Hook** | Block commits with insufficient documentation |
| 🤖 **GitHub Actions CI** | Enforce coverage and PEP 257 on every push/PR |

---

## Installation

```bash
pip install docgen
```

For development:

```bash
git clone https://github.com/your-org/docgen.git
cd docgen
pip install -e ".[dev]"
pre-commit install
```

---

## Quick Start

### Streamlit UI

```bash
docgen ui
```

Opens an interactive dashboard in your browser where you can:
- Upload `.py` files
- View coverage metrics and per-object breakdowns
- Generate and preview docstrings in any style
- See PEP 257 violations with severity badges
- Download patched files with docstrings inserted

### CLI

```bash
# Analyze a file or directory
docgen analyze src/

# Check docstring coverage
docgen coverage src/ --fail-under 80

# Validate PEP 257 compliance
docgen validate src/ --ignore D100,D104

# Generate and insert docstrings
docgen generate src/my_module.py --style google

# Preview changes without writing (dry run)
docgen generate src/my_module.py --dry-run

# Full combined report
docgen report src/ --json

# Scan a folder recursively
docgen scan src/ --recursive
```

### Python Library API

```python
from docgen import (
    analyze_code,
    generate_docstrings,
    validate_pep257,
    generate_coverage_report,
    load_project_config,
)
from pathlib import Path

# Analyze a file
module = analyze_code(Path("src/my_module.py"))

for func in module.functions:
    print(f"{func.name}: documented={func.has_docstring}")

# Generate docstrings for all undocumented objects
docstrings = generate_docstrings(module, style="google")
for name, doc in docstrings.items():
    print(f"\n--- {name} ---\n{doc}")

# Coverage report
report = generate_coverage_report(Path("src/my_module.py"))
print(f"Coverage: {report.coverage_pct:.1f}%")

# PEP 257 validation
val = validate_pep257(Path("src/my_module.py"), ignore_codes=["D100"])
for v in val.violations:
    print(f"  [{v.severity}] {v.code} L{v.lineno}: {v.message}")

# Load project config from pyproject.toml
cfg = load_project_config()
print(cfg.style, cfg.fail_under)
```

---

## Configuration

Add a `[tool.docgen]` section to your `pyproject.toml`:

```toml
[tool.docgen]
style = "google"          # google | numpy | rest | pep257
ignore = ["D100", "D104"] # pydocstyle codes to suppress
recursive = true
output_format = "json"    # text | json
fail_under = 80           # minimum coverage % (0-100)
include_private = false   # include _private functions
```

---

## CLI Reference

### `docgen analyze <target>`

Parse and display AST metadata.

| Option | Description |
|---|---|
| `--recursive / --no-recursive` | Recurse into directories |
| `--json` | Output as JSON |

### `docgen coverage <target>`

Show docstring coverage statistics.

| Option | Description |
|---|---|
| `--fail-under FLOAT` | Exit 1 if coverage is below this percentage |
| `--recursive / --no-recursive` | Recurse into directories |
| `--json` | Output as JSON |

### `docgen validate <target>`

Run PEP 257 compliance checks.

| Option | Description |
|---|---|
| `--ignore CODES` | Comma-separated codes to ignore (e.g. `D100,D104`) |
| `--recursive / --no-recursive` | Recurse into directories |
| `--json` | Output as JSON |

### `docgen generate <filepath>`

Insert docstrings into a Python file.

| Option | Description |
|---|---|
| `--style` | Docstring style: `google`, `numpy`, `rest`, `pep257` |
| `--output / -o` | Write to a different file |
| `--dry-run` | Print unified diff without writing |
| `--skip-existing / --overwrite` | Skip already-documented objects |

### `docgen report <target>`

Full combined analysis + coverage + validation report.

### `docgen scan <folder>`

Alias for `analyze` focused on directory scanning.

### `docgen ui`

Launch the Streamlit dashboard.

| Option | Description |
|---|---|
| `--port` | Server port (default: 8501) |

---

## Pre-commit Integration

After `pip install pre-commit` and `pre-commit install`, the hooks defined in `.pre-commit-config.yaml` will automatically:

1. **Check docstring coverage** — blocks commit if below threshold
2. **Run PEP 257 validation** — flags missing/malformed docstrings
3. **Run the test suite** — ensures nothing is broken

---

## CI / GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on every push and pull request:

1. **Tests** on Python 3.8–3.12 with coverage reporting
2. **Docstring coverage gate** — fails if below 80%
3. **PEP 257 validation**
4. **Ruff linting**
5. **Package build** — ensures the wheel is valid

Merge is blocked unless all checks pass.

---

## Edge Cases Handled

- Empty Python files
- Files with only comments
- Syntax errors (reported gracefully)
- Non-Python files (skipped)
- Invalid encoding (reported as encoding error)
- Nested functions (detected and marked)
- Decorated functions (decorators extracted)
- Async functions and methods
- Classes with no methods
- Already-documented functions (skippable)
- Empty folders

---

## Supported Docstring Styles

### Google

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a (int): First number.
        b (int): Second number.

    Returns:
        int: The sum.
    """
```

### NumPy

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    Parameters
    ----------
    a : int
        First number.
    b : int
        Second number.

    Returns
    -------
    int
        The sum.
    """
```

### reStructuredText

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    :param a: First number.
    :type a: int
    :param b: Second number.
    :type b: int
    :returns: The sum.
    :rtype: int
    """
```

### PEP 257

```python
def add(a: int, b: int) -> int:
    """Add two numbers."""
```

---

## Running Tests

```bash
# Full test suite with coverage
pytest

# Fast run (no coverage)
pytest -x -q

# Specific test file
pytest tests/test_analyzer.py -v
```

Coverage target: **90%+**

---

## Project Structure

```
docgen/
├── pyproject.toml
├── README.md
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── docgen/
│       ├── __init__.py          # Public API
│       ├── analyzer.py          # AST parser
│       ├── generator.py         # Docstring generator
│       ├── coverage.py          # Coverage engine
│       ├── validator.py         # PEP 257 validator
│       ├── configloader.py      # pyproject.toml reader
│       ├── cli.py               # Click CLI
│       └── uiapp.py             # Streamlit UI
└── tests/
    ├── conftest.py
    ├── test_analyzer.py
    ├── test_generator.py
    ├── test_coverage.py
    ├── test_validator.py
    ├── test_cli.py
    └── test_configloader.py
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes and add tests
4. Run `pre-commit run --all-files` and `pytest`
5. Open a pull request

---

## License

MIT License. See [LICENSE](LICENSE) for details.
