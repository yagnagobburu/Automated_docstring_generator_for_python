"""Project configuration loader.

Reads ``[tool.docgen]`` settings from ``pyproject.toml`` (walking up from the
current working directory) and exposes them as a typed :class:`DocgenConfig`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class DocgenConfig:
    """Resolved configuration for the docgen tool.

    All values fall back to sensible defaults when not specified in
    ``pyproject.toml``.

    Attributes:
        style: Docstring style – ``"google"``, ``"numpy"``, ``"rest"``,
            or ``"pep257"``.
        ignore: pydocstyle rule codes to suppress.
        recursive: Scan directories recursively.
        output_format: Report output format – ``"text"`` or ``"json"``.
        fail_under: Minimum coverage percentage before the tool exits
            non-zero (pre-commit / CI use).
        include_private: Include private objects (names starting with ``_``).
        config_file: Path of the ``pyproject.toml`` that was loaded, or
            ``None`` if defaults are used.
    """

    style: str = "google"
    ignore: List[str] = field(default_factory=list)
    recursive: bool = True
    output_format: str = "text"
    fail_under: float = 80.0
    include_private: bool = False
    config_file: Optional[str] = None


def _find_pyproject(start: Path) -> Optional[Path]:
    """Walk up from *start* looking for a ``pyproject.toml`` file.

    Args:
        start: Directory to begin the search.

    Returns:
        The resolved :class:`~pathlib.Path` of the first ``pyproject.toml``
        found, or ``None`` if the filesystem root is reached.
    """
    current = start.resolve()
    for parent in [current, *current.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


def _read_toml(path: Path) -> dict:
    """Read a TOML file, using the stdlib on Python 3.11+ or ``tomli`` otherwise.

    Args:
        path: Path to the ``.toml`` file.

    Returns:
        Parsed dict representation of the file.
    """
    if sys.version_info >= (3, 11):
        import tomllib  # type: ignore[import]
        with path.open("rb") as fh:
            return tomllib.load(fh)
    else:
        try:
            import tomli  # type: ignore[import]
            with path.open("rb") as fh:
                return tomli.load(fh)
        except ImportError:
            # Graceful fallback: no config
            return {}


def load_project_config(start: str | Path | None = None) -> DocgenConfig:
    """Load docgen settings from the nearest ``pyproject.toml``.

    Searches the directory tree upward from *start* (defaults to the current
    working directory) for a ``pyproject.toml`` containing a
    ``[tool.docgen]`` section.

    Args:
        start: Starting directory for the search. Defaults to ``Path.cwd()``.

    Returns:
        A :class:`DocgenConfig` populated from the file, or with defaults
        when no configuration is found.

    Example::

        cfg = load_project_config()
        print(cfg.style)        # "google"
        print(cfg.fail_under)   # 80.0
    """
    start = Path(start) if start else Path.cwd()
    pyproject_path = _find_pyproject(start)

    cfg = DocgenConfig()

    if pyproject_path is None:
        return cfg

    try:
        data = _read_toml(pyproject_path)
    except Exception:
        return cfg

    tool_section: dict = data.get("tool", {}).get("docgen", {})
    if not tool_section:
        return cfg

    cfg.config_file = str(pyproject_path)
    cfg.style = tool_section.get("style", cfg.style)
    cfg.ignore = tool_section.get("ignore", cfg.ignore)
    cfg.recursive = tool_section.get("recursive", cfg.recursive)
    cfg.output_format = tool_section.get("output_format", cfg.output_format)
    cfg.fail_under = float(tool_section.get("fail_under", cfg.fail_under))
    cfg.include_private = tool_section.get("include_private", cfg.include_private)

    return cfg
