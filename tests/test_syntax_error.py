"""Tests for syntax error handling across the docgen toolchain."""

import pytest
from docgen.analyzer import analyze_code
from docgen.coverage import generate_coverage_report
from docgen.generator import generate_docstrings, insert_docstrings_into_source


SYNTAX_ERROR_SOURCE = "def broken(:\n    pass\n"
VALID_SOURCE = "def add(a, b):\n    return a + b\n"


class TestSyntaxError:
    """Verify the tool handles syntax errors gracefully without crashing."""

    def test_analyzer_reports_syntax_error(self):
        """Analyzer should return a SyntaxError message, not raise an exception."""
        module = analyze_code(SYNTAX_ERROR_SOURCE)
        assert module.syntax_error is not None
        assert "SyntaxError" in module.syntax_error

    def test_analyzer_syntax_error_has_line_number(self):
        """The syntax error message should include the offending line number."""
        module = analyze_code(SYNTAX_ERROR_SOURCE)
        assert "line" in module.syntax_error.lower()

    def test_analyzer_no_functions_on_syntax_error(self):
        """No functions should be extracted when the file has a syntax error."""
        module = analyze_code(SYNTAX_ERROR_SOURCE)
        assert module.functions == []
        assert module.classes == []

    def test_coverage_handles_syntax_error(self):
        """Coverage report should record the error without crashing."""
        report = generate_coverage_report(SYNTAX_ERROR_SOURCE)
        assert report.syntax_error is not None

    def test_coverage_syntax_error_has_zero_objects(self):
        """A file with a syntax error should report zero documentable objects."""
        report = generate_coverage_report(SYNTAX_ERROR_SOURCE)
        assert report.total_objects == 0

    def test_generate_docstrings_on_syntax_error(self):
        """Docstring generator should return an empty dict for broken source."""
        module = analyze_code(SYNTAX_ERROR_SOURCE)
        result = generate_docstrings(module)
        assert result == {}

    def test_insert_docstrings_returns_string_on_syntax_error(self):
        """insert_docstrings_into_source must return a string even for broken code."""
        module = analyze_code(SYNTAX_ERROR_SOURCE)
        result = insert_docstrings_into_source(SYNTAX_ERROR_SOURCE, module)
        assert isinstance(result, str)

    def test_valid_source_has_no_syntax_error(self):
        """Sanity check — valid source should not trigger syntax error."""
        module = analyze_code(VALID_SOURCE)
        assert module.syntax_error is None

    def test_syntax_error_from_file(self, tmp_path):
        """Analyzer should handle a syntax-error .py file on disk correctly."""
        broken_file = tmp_path / "broken.py"
        broken_file.write_text(SYNTAX_ERROR_SOURCE, encoding="utf-8")
        module = analyze_code(broken_file)
        assert module.syntax_error is not None

    def test_multiple_syntax_errors_handled(self):
        """A file with multiple broken lines should still return one error report."""
        badly_broken = "def (\ndef (\ndef (\n"
        module = analyze_code(badly_broken)
        assert module.syntax_error is not None
        assert module.functions == []
