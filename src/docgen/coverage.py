"""Docstring coverage engine.

Computes how many functions, methods, and classes are documented versus
undocumented and produces human-readable or JSON coverage reports.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from docgen.analyzer import ClassInfo, FunctionInfo, ModuleInfo, analyze_code, analyze_folder


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ObjectCoverage:
    """Coverage result for a single documentable object."""

    name: str
    qualified_name: str
    kind: str               # "function" | "method" | "class" | "module"
    has_docstring: bool
    lineno: int = 0
    filepath: str = ""


@dataclass
class FileCoverageReport:
    """Coverage summary for a single Python file."""

    filepath: str
    total_objects: int = 0
    documented: int = 0
    undocumented: int = 0
    coverage_pct: float = 0.0
    objects: List[ObjectCoverage] = field(default_factory=list)
    syntax_error: Optional[str] = None
    encoding_error: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to a plain dict (JSON-serializable)."""
        return asdict(self)


@dataclass
class ProjectCoverageReport:
    """Aggregated coverage across multiple files."""

    files: List[FileCoverageReport] = field(default_factory=list)
    total_objects: int = 0
    documented: int = 0
    undocumented: int = 0
    coverage_pct: float = 0.0

    def passes_threshold(self, threshold: float) -> bool:
        """Check whether overall coverage meets a minimum threshold.

        Args:
            threshold: Minimum required coverage percentage (0–100).

        Returns:
            bool: True if coverage_pct >= threshold.
        """
        return self.coverage_pct >= threshold

    def to_dict(self) -> dict:
        """Serialize to a plain dict."""
        return {
            "total_objects": self.total_objects,
            "documented": self.documented,
            "undocumented": self.undocumented,
            "coverage_pct": round(self.coverage_pct, 2),
            "files": [f.to_dict() for f in self.files],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _module_to_file_report(module: ModuleInfo, include_private: bool = False) -> FileCoverageReport:
    report = FileCoverageReport(filepath=module.filepath)

    if module.syntax_error:
        report.syntax_error = module.syntax_error
        return report
    if module.encoding_error:
        report.encoding_error = module.encoding_error
        return report

    objects: List[ObjectCoverage] = []

    # Module-level docstring
    objects.append(ObjectCoverage(
        name="<module>",
        qualified_name=module.filepath,
        kind="module",
        has_docstring=module.has_module_docstring,
        filepath=module.filepath,
    ))

    def _add_func(func: FunctionInfo) -> None:
        if func.is_nested:
            return
        if not include_private and func.is_private:
            return
        objects.append(ObjectCoverage(
            name=func.name,
            qualified_name=func.qualified_name,
            kind=func.kind,
            has_docstring=func.has_docstring,
            lineno=func.lineno,
            filepath=module.filepath,
        ))

    for func in module.functions:
        _add_func(func)

    for cls in module.classes:
        if include_private or not cls.name.startswith("_"):
            objects.append(ObjectCoverage(
                name=cls.name,
                qualified_name=cls.name,
                kind="class",
                has_docstring=cls.has_docstring,
                lineno=cls.lineno,
                filepath=module.filepath,
            ))
        for method in cls.methods:
            _add_func(method)

    documented = sum(1 for o in objects if o.has_docstring)
    total = len(objects)

    report.total_objects = total
    report.documented = documented
    report.undocumented = total - documented
    report.coverage_pct = (documented / total * 100) if total else 100.0
    report.objects = objects
    return report


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_coverage_report(
    source: str | Path,
    include_private: bool = False,
) -> FileCoverageReport:
    """Generate a docstring coverage report for a single Python file.

    Args:
        source: File path or raw Python source code string.
        include_private: Whether to include private objects.

    Returns:
        :class:`FileCoverageReport` with per-object coverage details.
    """
    module = analyze_code(source)
    return _module_to_file_report(module, include_private=include_private)


def generate_folder_coverage(
    folder: str | Path,
    recursive: bool = True,
    include_private: bool = False,
) -> ProjectCoverageReport:
    """Generate aggregated docstring coverage for an entire directory.

    Args:
        folder: Path to the directory to scan.
        recursive: Descend into sub-directories.
        include_private: Include private objects.

    Returns:
        :class:`ProjectCoverageReport` aggregating all files.
    """
    modules = analyze_folder(folder, recursive=recursive, include_private=include_private)
    project = ProjectCoverageReport()

    for module in modules:
        file_report = _module_to_file_report(module, include_private=include_private)
        project.files.append(file_report)
        project.total_objects += file_report.total_objects
        project.documented += file_report.documented
        project.undocumented += file_report.undocumented

    if project.total_objects:
        project.coverage_pct = project.documented / project.total_objects * 100

    return project
