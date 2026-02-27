"""Tests for empty file and edge case handling across the docgen toolchain."""

import pytest
from docgen.analyzer import analyze_code, analyze_folder
from docgen.coverage import generate_coverage_report, generate_folder_coverage
from docgen.generator import generate_docstrings, insert_docstrings_into_source


EMPTY_SOURCE = ""
WHITESPACE_ONLY = "   \n\n   \n"
COMMENTS_ONLY = "# This is a comment\n# Another comment\n"
NEWLINES_ONLY = "\n\n\n\n"


class TestEmptyFile:
    """Verify the tool handles empty and near-empty files without crashing."""

    def test_analyzer_empty_string(self):
        """Analyzing an empty string should return a valid ModuleInfo."""
        module = analyze_code(EMPTY_SOURCE)
        assert module.syntax_error is None
        assert module.functions == []
        assert module.classes == []

    def test_analyzer_whitespace_only(self):
        """A file with only whitespace should parse cleanly."""
        module = analyze_code(WHITESPACE_ONLY)
        assert module.syntax_error is None
        assert module.functions == []

    def test_analyzer_comments_only(self):
        """A file with only comments should have no functions or classes."""
        module = analyze_code(COMMENTS_ONLY)
        assert module.syntax_error is None
        assert module.functions == []
        assert module.classes == []

    def test_analyzer_newlines_only(self):
        """A file with only newlines should parse cleanly."""
        module = analyze_code(NEWLINES_ONLY)
        assert module.syntax_error is None

    def test_coverage_empty_file(self):
        """Coverage report for an empty file should not crash."""
        report = generate_coverage_report(EMPTY_SOURCE)
        assert report is not None
        assert 0.0 <= report.coverage_pct <= 100.0

    def test_coverage_comments_only(self):
        """Coverage report for a comments-only file should show no functions."""
        report = generate_coverage_report(COMMENTS_ONLY)
        func_objects = [o for o in report.objects if "function" in o.kind]
        assert func_objects == []

    def test_generate_docstrings_empty_module(self):
        """Generating docstrings for an empty module should return an empty dict."""
        module = analyze_code(EMPTY_SOURCE)
        result = generate_docstrings(module)
        assert result == {}

    def test_insert_docstrings_empty_source(self):
        """Inserting into empty source should return a string (possibly empty)."""
        module = analyze_code(EMPTY_SOURCE)
        result = insert_docstrings_into_source(EMPTY_SOURCE, module)
        assert isinstance(result, str)

    def test_empty_file_on_disk(self, tmp_path):
        """An empty .py file on disk should be parsed without errors."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("", encoding="utf-8")
        module = analyze_code(empty_file)
        assert module.syntax_error is None
        assert module.functions == []

    def test_empty_folder(self, tmp_path):
        """Scanning an empty folder should return an empty list."""
        results = analyze_folder(tmp_path)
        assert results == []

    def test_folder_coverage_empty_folder(self, tmp_path):
        """Coverage for an empty folder should report zero objects."""
        report = generate_folder_coverage(tmp_path)
        assert report.total_objects == 0

    def test_folder_with_only_empty_files(self, tmp_path):
        """A folder containing only empty .py files should still be scanned."""
        (tmp_path / "a.py").write_text("", encoding="utf-8")
        (tmp_path / "b.py").write_text("", encoding="utf-8")
        results = analyze_folder(tmp_path)
        assert len(results) == 2
        for module in results:
            assert module.functions == []
            assert module.classes == []
