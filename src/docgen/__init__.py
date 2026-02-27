"""docgen — Automated Python Docstring Generator, Validator & Coverage Suite.

Provides three entry points:
  • ``docgen ui``          — Launch the interactive Streamlit dashboard
  • ``docgen <command>``   — Full-featured CLI
  • ``import docgen``      — Pip-installable Python library API

Example::

    from docgen import analyze_code, generate_docstrings, validate_pep257, generate_coverage_report

    results = analyze_code("my_module.py")
    report  = generate_coverage_report("my_module.py")
"""

from docgen.analyzer import analyze_code
from docgen.generator import generate_docstring, generate_docstrings
from docgen.coverage import generate_coverage_report
from docgen.validator import validate_pep257
from docgen.configloader import load_project_config

__all__ = [
    "analyze_code",
    "generate_docstring",
    "generate_docstrings",
    "validate_pep257",
    "generate_coverage_report",
    "load_project_config",
]

__version__ = "1.0.0"
