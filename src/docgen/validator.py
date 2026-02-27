"""PEP 257 docstring validator powered by pydocstyle.

Runs ``pydocstyle`` on Python source files and returns structured violation
objects that can be consumed by the CLI, Streamlit UI, or library users.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    """A single PEP 257 violation reported by pydocstyle."""

    filepath: str
    lineno: int
    code: str           # e.g. "D100"
    message: str        # Human-readable description
    severity: str       # "error" | "warning"  (D4xx → warning, rest → error)
    object_name: str = ""  # Extracted from the pydocstyle output when available


@dataclass
class ValidationReport:
    """Aggregated PEP 257 validation results for one or more files."""

    filepath: str
    violations: List[Violation] = field(default_factory=list)
    pydocstyle_available: bool = True
    error_message: Optional[str] = None

    @property
    def total(self) -> int:
        """Total number of violations."""
        return len(self.violations)

    @property
    def errors(self) -> List[Violation]:
        """Violations classified as errors."""
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> List[Violation]:
        """Violations classified as warnings."""
        return [v for v in self.violations if v.severity == "warning"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_WARNING_CODES = frozenset({"D400", "D401", "D402", "D403", "D404", "D405",
                             "D406", "D407", "D408", "D409", "D410", "D411",
                             "D412", "D413", "D414", "D415", "D416", "D417",
                             "D418", "D419"})


def _severity(code: str) -> str:
    return "warning" if code in _WARNING_CODES else "error"


def _parse_pydocstyle_output(output: str, filepath: str) -> List[Violation]:
    """Parse raw pydocstyle stdout into :class:`Violation` objects.

    pydocstyle output format (two lines per violation)::

        path/to/file.py:10 in public function `my_func`:
                D103: Missing docstring in public function

    Args:
        output: Raw text output from pydocstyle.
        filepath: The file that was analyzed.

    Returns:
        List of :class:`Violation` objects.
    """
    violations: List[Violation] = []
    lines = output.strip().splitlines()
    i = 0
    while i < len(lines) - 1:
        loc_line = lines[i].strip()
        msg_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
        i += 2

        if not loc_line or not msg_line:
            continue

        # Parse location line:  "<file>:<lineno> in <context>:"
        try:
            loc_part, _, context = loc_line.partition(" in ")
            file_part, _, lineno_str = loc_part.rpartition(":")
            lineno = int(lineno_str) if lineno_str.isdigit() else 0
            object_name = context.rstrip(":").strip()
        except Exception:
            lineno = 0
            object_name = ""

        # Parse message line:  "D103: Missing docstring in public function"
        if ":" in msg_line:
            code_part, _, message = msg_line.partition(":")
            code = code_part.strip()
            message = message.strip()
        else:
            code = "D000"
            message = msg_line

        violations.append(
            Violation(
                filepath=filepath,
                lineno=lineno,
                code=code,
                message=message,
                severity=_severity(code),
                object_name=object_name,
            )
        )

    return violations


def _run_pydocstyle(filepath: str, ignore_codes: list[str] | None = None) -> tuple[str, str, int]:
    """Execute pydocstyle as a subprocess.

    Args:
        filepath: Path to the Python file to validate.
        ignore_codes: List of violation codes to suppress (e.g. ["D100"]).

    Returns:
        Tuple of (stdout, stderr, returncode).
    """
    cmd = [sys.executable, "-m", "pydocstyle", filepath]
    if ignore_codes:
        cmd += ["--add-ignore=" + ",".join(ignore_codes)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_pep257(
    source: str | Path,
    ignore_codes: list[str] | None = None,
    filepath_label: str = "<string>",
) -> ValidationReport:
    """Validate PEP 257 compliance for a Python file or source string.

    Args:
        source: File path (Path/str) or raw Python source code string.
        ignore_codes: pydocstyle rule codes to ignore, e.g. ``["D100", "D104"]``.
        filepath_label: Display label used when ``source`` is raw code.

    Returns:
        :class:`ValidationReport` with all violations found.

    Example::

        report = validate_pep257(Path("my_module.py"), ignore_codes=["D100"])
        for v in report.violations:
            print(f"  {v.code} L{v.lineno}: {v.message}")
    """
    # Check if pydocstyle is importable
    try:
        import pydocstyle  # noqa: F401
    except ImportError:
        return ValidationReport(
            filepath=filepath_label,
            pydocstyle_available=False,
            error_message="pydocstyle is not installed. Run: pip install pydocstyle",
        )

    # Determine actual file path
    tmp_file = None
    if isinstance(source, Path) or (isinstance(source, str) and Path(source).exists()):
        actual_path = str(source)
        filepath_label = actual_path
    else:
        # Write raw source to a temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8")
        tmp.write(source)
        tmp.flush()
        tmp_file = tmp.name
        actual_path = tmp_file

    try:
        stdout, stderr, _ = _run_pydocstyle(actual_path, ignore_codes=ignore_codes)
        violations = _parse_pydocstyle_output(stdout, filepath=filepath_label)
        report = ValidationReport(filepath=filepath_label, violations=violations)
        if stderr and "Error" in stderr:
            report.error_message = stderr.strip()
    except Exception as exc:
        report = ValidationReport(
            filepath=filepath_label,
            error_message=str(exc),
        )
    finally:
        if tmp_file:
            Path(tmp_file).unlink(missing_ok=True)

    return report


def validate_folder(
    folder: str | Path,
    recursive: bool = True,
    ignore_codes: list[str] | None = None,
) -> List[ValidationReport]:
    """Validate all Python files in a directory.

    Args:
        folder: Directory to scan.
        recursive: Descend into sub-directories.
        ignore_codes: pydocstyle codes to suppress.

    Returns:
        List of :class:`ValidationReport` objects, one per file.
    """
    folder = Path(folder)
    pattern = "**/*.py" if recursive else "*.py"
    return [
        validate_pep257(py_file, ignore_codes=ignore_codes)
        for py_file in sorted(folder.glob(pattern))
    ]
