"""AST-based Python code analyzer.

Parses Python source files and extracts metadata about functions, classes,
methods, parameters, return annotations, and existing docstrings.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParamInfo:
    """Metadata for a single function/method parameter."""

    name: str
    annotation: Optional[str] = None
    default: Optional[str] = None


@dataclass
class FunctionInfo:
    """Metadata for a function or method extracted from AST."""

    name: str
    qualified_name: str          # e.g. "MyClass.my_method"
    kind: str                    # "function" | "method" | "async_function" | "async_method"
    params: List[ParamInfo] = field(default_factory=list)
    return_annotation: Optional[str] = None
    existing_docstring: Optional[str] = None
    has_docstring: bool = False
    decorators: List[str] = field(default_factory=list)
    lineno: int = 0
    is_private: bool = False
    is_nested: bool = False


@dataclass
class ClassInfo:
    """Metadata for a class extracted from AST."""

    name: str
    bases: List[str] = field(default_factory=list)
    existing_docstring: Optional[str] = None
    has_docstring: bool = False
    methods: List[FunctionInfo] = field(default_factory=list)
    lineno: int = 0
    decorators: List[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Top-level result of analyzing a single Python file."""

    filepath: str
    module_docstring: Optional[str] = None
    has_module_docstring: bool = False
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    syntax_error: Optional[str] = None
    encoding_error: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _annotation_to_str(node: Optional[ast.expr]) -> Optional[str]:
    """Convert an AST annotation node to a readable string."""
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _get_decorators(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> List[str]:
    """Return decorator names as strings."""
    result = []
    for d in node.decorator_list:
        try:
            result.append(ast.unparse(d))
        except Exception:
            result.append("<decorator>")
    return result


def _extract_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[ParamInfo]:
    """Extract parameter metadata from a function/method AST node."""
    params: List[ParamInfo] = []
    args = node.args

    # Build defaults map (only non-None defaults aligned from the right)
    all_args = args.posonlyargs + args.args
    defaults_offset = len(all_args) - len(args.defaults)

    for i, arg in enumerate(all_args):
        if arg.arg in ("self", "cls"):
            continue
        default_val: Optional[str] = None
        default_index = i - defaults_offset
        if default_index >= 0 and default_index < len(args.defaults):
            try:
                default_val = ast.unparse(args.defaults[default_index])
            except Exception:
                default_val = "..."
        params.append(
            ParamInfo(
                name=arg.arg,
                annotation=_annotation_to_str(arg.annotation),
                default=default_val,
            )
        )

    # *args
    if args.vararg:
        params.append(ParamInfo(name=f"*{args.vararg.arg}", annotation=_annotation_to_str(args.vararg.annotation)))

    # **kwargs
    if args.kwarg:
        params.append(ParamInfo(name=f"**{args.kwarg.arg}", annotation=_annotation_to_str(args.kwarg.annotation)))

    return params


def _is_private(name: str) -> bool:
    return name.startswith("_") and not name.startswith("__")


def _visit_functions(
    nodes: list,
    parent_class: Optional[str],
    is_nested: bool = False,
) -> List[FunctionInfo]:
    """Recursively visit function nodes in an AST body."""
    result: List[FunctionInfo] = []
    for node in nodes:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        kind_prefix = "async_" if isinstance(node, ast.AsyncFunctionDef) else ""
        kind_suffix = "method" if parent_class else "function"
        kind = kind_prefix + kind_suffix

        qualified = f"{parent_class}.{node.name}" if parent_class else node.name
        docstring = ast.get_docstring(node)

        func_info = FunctionInfo(
            name=node.name,
            qualified_name=qualified,
            kind=kind,
            params=_extract_params(node),
            return_annotation=_annotation_to_str(node.returns),
            existing_docstring=docstring,
            has_docstring=bool(docstring),
            decorators=_get_decorators(node),
            lineno=node.lineno,
            is_private=_is_private(node.name),
            is_nested=is_nested,
        )
        result.append(func_info)

        # Recurse into nested functions (but mark them as nested)
        nested = _visit_functions(node.body, parent_class=None, is_nested=True)
        result.extend(nested)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_code(source: str | Path, filepath: str = "<string>") -> ModuleInfo:
    """Analyze Python source code and return structured metadata.

    Args:
        source: Either a file path (Path or str) or raw Python source code.
        filepath: Label used in the returned ``ModuleInfo`` when ``source`` is
            raw code rather than a file path.

    Returns:
        A :class:`ModuleInfo` instance describing the parsed module.

    Example::

        info = analyze_code(Path("my_module.py"))
        for func in info.functions:
            print(func.name, func.has_docstring)
    """
    # Resolve source text
    if isinstance(source, Path) or (isinstance(source, str) and os.path.exists(source)):
        path = Path(source)
        filepath = str(path)
        try:
            source_text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return ModuleInfo(filepath=filepath, encoding_error=str(exc))
        except FileNotFoundError:
            return ModuleInfo(filepath=filepath, syntax_error="File not found")
    else:
        source_text = source  # type: ignore[assignment]

    # Handle empty file
    if not source_text or not source_text.strip():
        return ModuleInfo(filepath=filepath)

    # Parse AST
    try:
        tree = ast.parse(source_text, filename=filepath)
    except SyntaxError as exc:
        return ModuleInfo(filepath=filepath, syntax_error=f"SyntaxError at line {exc.lineno}: {exc.msg}")

    module_doc = ast.get_docstring(tree)
    info = ModuleInfo(
        filepath=filepath,
        module_docstring=module_doc,
        has_module_docstring=bool(module_doc),
    )

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Top-level function
            for func in _visit_functions([node], parent_class=None):
                info.functions.append(func)

        elif isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node)
            class_info = ClassInfo(
                name=node.name,
                bases=[_annotation_to_str(b) or "" for b in node.bases],
                existing_docstring=docstring,
                has_docstring=bool(docstring),
                lineno=node.lineno,
                decorators=_get_decorators(node),
            )
            # Methods
            for method in _visit_functions(node.body, parent_class=node.name):
                class_info.methods.append(method)

            info.classes.append(class_info)

    return info


def analyze_folder(
    folder: str | Path,
    recursive: bool = True,
    include_private: bool = False,
) -> List[ModuleInfo]:
    """Analyze all Python files inside a directory.

    Args:
        folder: Path to the directory to scan.
        recursive: Whether to descend into sub-directories.
        include_private: Include files whose names start with ``_``.

    Returns:
        A list of :class:`ModuleInfo` objects, one per ``.py`` file found.
    """
    folder = Path(folder)
    if not folder.exists():
        return []

    pattern = "**/*.py" if recursive else "*.py"
    results: List[ModuleInfo] = []
    for py_file in sorted(folder.glob(pattern)):
        if not include_private and py_file.stem.startswith("_") and py_file.stem != "__init__":
            continue
        results.append(analyze_code(py_file))

    return results
