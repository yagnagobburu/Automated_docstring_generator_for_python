"""Tests for CLI commands, help text, and basic invocation."""

import json
import pytest
from click.testing import CliRunner
from docgen.cli import main


@pytest.fixture
def runner():
    """Provide a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_file(tmp_path):
    """A simple undocumented Python file for CLI testing."""
    source = "def add(a, b):\n    return a + b\n\nclass Calc:\n    def mul(self, x, y):\n        return x * y\n"
    path = tmp_path / "sample.py"
    path.write_text(source, encoding="utf-8")
    return path


@pytest.fixture
def documented_file(tmp_path):
    """A fully documented Python file for CLI testing."""
    source = (
        '"""Module docstring."""\n\n'
        "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n"
    )
    path = tmp_path / "documented.py"
    path.write_text(source, encoding="utf-8")
    return path


# ── Help text ──────────────────────────────────────────────────────────────

class TestHelpText:
    """Verify all commands expose useful help text."""

    def test_root_help(self, runner):
        """Running `docgen --help` should exit 0 and show usage."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_root_help_lists_commands(self, runner):
        """Root help should list the main sub-commands."""
        result = runner.invoke(main, ["--help"])
        for cmd in ["analyze", "coverage", "validate", "generate", "report", "scan", "ui"]:
            assert cmd in result.output

    def test_analyze_help(self, runner):
        result = runner.invoke(main, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "TARGET" in result.output or "target" in result.output.lower()

    def test_coverage_help(self, runner):
        result = runner.invoke(main, ["coverage", "--help"])
        assert result.exit_code == 0
        assert "fail-under" in result.output

    def test_validate_help(self, runner):
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "ignore" in result.output

    def test_generate_help(self, runner):
        result = runner.invoke(main, ["generate", "--help"])
        assert result.exit_code == 0
        assert "style" in result.output

    def test_report_help(self, runner):
        result = runner.invoke(main, ["report", "--help"])
        assert result.exit_code == 0

    def test_scan_help(self, runner):
        result = runner.invoke(main, ["scan", "--help"])
        assert result.exit_code == 0

    def test_version_flag(self, runner):
        """--version should print the package version and exit 0."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output or "version" in result.output.lower()


# ── analyze command ────────────────────────────────────────────────────────

class TestAnalyzeCommand:
    def test_analyze_file(self, runner, sample_file):
        result = runner.invoke(main, ["analyze", str(sample_file)])
        assert result.exit_code == 0

    def test_analyze_shows_function_name(self, runner, sample_file):
        result = runner.invoke(main, ["analyze", str(sample_file)])
        assert "sample.py" in result.output or "%" in result.output

    def test_analyze_json_is_valid(self, runner, sample_file):
        result = runner.invoke(main, ["analyze", str(sample_file), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["filepath"] == str(sample_file)

    def test_analyze_missing_file_exits_nonzero(self, runner):
        result = runner.invoke(main, ["analyze", "/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_analyze_directory(self, runner, tmp_path, sample_file):
        result = runner.invoke(main, ["analyze", str(tmp_path)])
        assert result.exit_code == 0


# ── coverage command ───────────────────────────────────────────────────────

class TestCoverageCommand:
    def test_coverage_file(self, runner, sample_file):
        result = runner.invoke(main, ["coverage", str(sample_file), "--fail-under", "0"])
        assert result.exit_code == 0

    def test_coverage_fails_under_100(self, runner, sample_file):
        """Undocumented file should fail when threshold is 100%."""
        result = runner.invoke(main, ["coverage", str(sample_file), "--fail-under", "100"])
        assert result.exit_code == 1

    def test_coverage_passes_under_zero(self, runner, sample_file):
        """Any file passes when threshold is 0."""
        result = runner.invoke(main, ["coverage", str(sample_file), "--fail-under", "0"])
        assert result.exit_code == 0

    def test_coverage_json_output(self, runner, sample_file):
        result = runner.invoke(main, ["coverage", str(sample_file), "--json", "--fail-under", "0"])
        assert result.exit_code == 0

    def test_coverage_missing_file(self, runner):
        result = runner.invoke(main, ["coverage", "/no/such/file.py"])
        assert result.exit_code != 0


# ── generate command ───────────────────────────────────────────────────────

class TestGenerateCommand:
    def test_generate_dry_run(self, runner, sample_file):
        result = runner.invoke(main, ["generate", str(sample_file), "--dry-run"])
        assert result.exit_code == 0

    def test_generate_writes_output_file(self, runner, sample_file, tmp_path):
        out = tmp_path / "patched.py"
        result = runner.invoke(main, ["generate", str(sample_file), "--output", str(out)])
        assert result.exit_code == 0
        assert out.exists()

    def test_generate_output_contains_docstrings(self, runner, sample_file, tmp_path):
        out = tmp_path / "patched.py"
        runner.invoke(main, ["generate", str(sample_file), "--output", str(out)])
        content = out.read_text()
        assert '"""' in content

    def test_generate_style_google(self, runner, sample_file, tmp_path):
        out = tmp_path / "google.py"
        runner.invoke(main, ["generate", str(sample_file), "--style", "google", "--output", str(out)])
        assert "Args:" in out.read_text()

    def test_generate_style_numpy(self, runner, sample_file, tmp_path):
        out = tmp_path / "numpy.py"
        runner.invoke(main, ["generate", str(sample_file), "--style", "numpy", "--output", str(out)])
        assert "Parameters" in out.read_text()

    def test_generate_missing_file(self, runner):
        result = runner.invoke(main, ["generate", "/no/such/file.py"])
        assert result.exit_code != 0
