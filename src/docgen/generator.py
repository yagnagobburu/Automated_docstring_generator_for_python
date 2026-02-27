"""Docstring generation engine supporting Google, NumPy, reST, and PEP 257 styles."""

from __future__ import annotations

from typing import Literal, Optional

from docgen.analyzer import ClassInfo, FunctionInfo, ModuleInfo, analyze_code

Style = Literal["google", "numpy", "rest", "pep257"]
VALID_STYLES: tuple[str, ...] = ("google", "numpy", "rest", "pep257")


# ---------------------------------------------------------------------------
# Low-level builders
# ---------------------------------------------------------------------------

def _indent(text: str, spaces: int = 4) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line.strip() else line for line in text.splitlines())


def _build_google(func: FunctionInfo) -> str:
    lines = [f'"""Summary line for {func.name}.']

    non_self = [p for p in func.params if p.name not in ("self", "cls")]

    if non_self:
        lines.append("")
        lines.append("    Args:")
        for p in non_self:
            type_hint = f" ({p.annotation})" if p.annotation else ""
            default_note = f" Defaults to {p.default}." if p.default is not None else ""
            lines.append(f"        {p.name}{type_hint}: Description.{default_note}")

    if func.return_annotation and func.return_annotation != "None":
        lines.append("")
        lines.append("    Returns:")
        lines.append(f"        {func.return_annotation}: Description.")

    lines.append('"""')
    return "\n".join(lines)


def _build_numpy(func: FunctionInfo) -> str:
    lines = [f'"""Summary line for {func.name}.',
             "",
             "    Extended description (optional).",
             ]

    non_self = [p for p in func.params if p.name not in ("self", "cls")]

    if non_self:
        lines += ["", "    Parameters", "    ----------"]
        for p in non_self:
            type_hint = f" : {p.annotation}" if p.annotation else ""
            lines.append(f"    {p.name}{type_hint}")
            lines.append("        Description.")

    if func.return_annotation and func.return_annotation != "None":
        lines += ["", "    Returns", "    -------"]
        lines.append(f"    {func.return_annotation}")
        lines.append("        Description.")

    lines.append('"""')
    return "\n".join(lines)


def _build_rest(func: FunctionInfo) -> str:
    lines = [f'"""Summary line for {func.name}.',
             "",
             "    Extended description (optional).",
             ""]

    non_self = [p for p in func.params if p.name not in ("self", "cls")]
    for p in non_self:
        lines.append(f"    :param {p.name}: Description.")
        if p.annotation:
            lines.append(f"    :type {p.name}: {p.annotation}")

    if func.return_annotation and func.return_annotation != "None":
        lines.append("    :returns: Description.")
        lines.append(f"    :rtype: {func.return_annotation}")

    lines.append('"""')
    return "\n".join(lines)


def _build_pep257(func: FunctionInfo) -> str:
    return f'"""Summary line for {func.name}."""'


def _build_class_google(cls: ClassInfo) -> str:
    lines = [f'"""Summary for class {cls.name}.',
             ""]
    if cls.bases:
        lines.append(f"    Inherits from: {', '.join(b for b in cls.bases if b)}.")
        lines.append("")

    lines += [
        "    Attributes:",
        "        attribute_name (type): Description.",
        '"""',
    ]
    return "\n".join(lines)


def _build_class_numpy(cls: ClassInfo) -> str:
    lines = [f'"""Summary for class {cls.name}.',
             "",
             "    Extended description (optional).",
             "",
             "    Attributes",
             "    ----------",
             "    attribute_name : type",
             "        Description.",
             '"""']
    return "\n".join(lines)


def _build_class_rest(cls: ClassInfo) -> str:
    return "\n".join([
        f'"""Summary for class {cls.name}.',
        "",
        "    Extended description (optional).",
        '"""'
    ])


def _build_class_pep257(cls: ClassInfo) -> str:
    return f'"""Summary for class {cls.name}."""'


_FUNC_BUILDERS = {
    "google": _build_google,
    "numpy": _build_numpy,
    "rest": _build_rest,
    "pep257": _build_pep257,
}

_CLASS_BUILDERS = {
    "google": _build_class_google,
    "numpy": _build_class_numpy,
    "rest": _build_class_rest,
    "pep257": _build_class_pep257,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_docstring(
    obj: FunctionInfo | ClassInfo,
    style: Style = "google",
) -> str:
    """Generate a docstring for a single function or class.

    Args:
        obj: A :class:`~docgen.analyzer.FunctionInfo` or
            :class:`~docgen.analyzer.ClassInfo` instance.
        style: One of ``"google"``, ``"numpy"``, ``"rest"``, ``"pep257"``.

    Returns:
        str: The generated docstring (without surrounding triple quotes
        indentation — ready to be inserted into source).

    Raises:
        ValueError: If an unsupported style is provided.
    """
    if style not in VALID_STYLES:
        raise ValueError(f"Unsupported style '{style}'. Choose from: {VALID_STYLES}")

    if isinstance(obj, FunctionInfo):
        return _FUNC_BUILDERS[style](obj)
    elif isinstance(obj, ClassInfo):
        return _CLASS_BUILDERS[style](obj)
    else:
        raise TypeError(f"Expected FunctionInfo or ClassInfo, got {type(obj).__name__}")


def generate_docstrings(
    module: ModuleInfo,
    style: Style = "google",
    skip_existing: bool = True,
    include_private: bool = False,
) -> dict[str, str]:
    """Generate docstrings for all undocumented objects in a module.

    Args:
        module: A :class:`~docgen.analyzer.ModuleInfo` result.
        style: Docstring style to use.
        skip_existing: If ``True``, skip objects that already have docstrings.
        include_private: Include private functions/methods (names starting
            with ``_``).

    Returns:
        dict[str, str]: Mapping of ``qualified_name`` → generated docstring.
    """
    results: dict[str, str] = {}

    def _should_include(obj: FunctionInfo | ClassInfo) -> bool:
        if skip_existing and (obj.has_docstring if hasattr(obj, "has_docstring") else False):
            return False
        if not include_private:
            name = obj.name
            if name.startswith("_") and not name.startswith("__"):
                return False
        return True

    # Module-level functions
    for func in module.functions:
        if not func.is_nested and _should_include(func):
            results[func.qualified_name] = generate_docstring(func, style)

    # Classes and their methods
    for cls in module.classes:
        if _should_include(cls):
            results[cls.name] = generate_docstring(cls, style)
        for method in cls.methods:
            if not method.is_nested and _should_include(method):
                results[method.qualified_name] = generate_docstring(method, style)

    return results


def insert_docstrings_into_source(
    source: str,
    module: ModuleInfo,
    style: Style = "google",
    skip_existing: bool = True,
) -> str:
    """Insert generated docstrings back into Python source code.

    This function rewrites the source by inserting docstrings immediately
    after ``def``/``class`` statement lines for undocumented objects.

    Args:
        source: Original Python source code as a string.
        module: Parsed :class:`~docgen.analyzer.ModuleInfo`.
        style: Docstring style for generation.
        skip_existing: Skip objects that already have docstrings.

    Returns:
        str: Modified source code with docstrings inserted.
    """
    import re

    lines = source.splitlines(keepends=True)
    generated = generate_docstrings(module, style=style, skip_existing=skip_existing)

    # Build a line-number → docstring map
    insertions: dict[int, str] = {}

    for func in module.functions:
        if func.qualified_name in generated:
            insertions[func.lineno] = generated[func.qualified_name]

    for cls in module.classes:
        if cls.name in generated:
            insertions[cls.lineno] = generated[cls.name]
        for method in cls.methods:
            if method.qualified_name in generated:
                insertions[method.lineno] = generated[method.qualified_name]

    if not insertions:
        return source

    # Find the body start line (line after def/class) for each target
    result_lines: list[str] = []
    i = 0
    while i < len(lines):
        lineno = i + 1  # 1-indexed
        result_lines.append(lines[i])

        if lineno in insertions:
            # Determine indent of the next non-empty line (body)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                result_lines.append(lines[j])
                j += 1
                i += 1

            # Detect body indentation
            if j < len(lines):
                body_indent = len(lines[j]) - len(lines[j].lstrip())
            else:
                body_indent = 4

            indent_str = " " * body_indent
            docstring = insertions[lineno]
            indented = "\n".join(
                indent_str + dl if dl.strip() else dl
                for dl in docstring.splitlines()
            )
            result_lines.append(indented + "\n")
        i += 1

    return "".join(result_lines)
