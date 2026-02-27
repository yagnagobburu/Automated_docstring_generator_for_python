# """Command-line interface for docgen.

# Usage examples::

#     docgen analyze src/
#     docgen coverage src/ --recursive
#     docgen validate src/my_module.py --ignore D100,D104
#     docgen generate src/my_module.py --style numpy --output out.py
#     docgen report src/ --json
#     docgen scan src/ --recursive
#     docgen ui
# """

# from __future__ import annotations

# import json
# import sys
# from pathlib import Path
# from typing import Optional

# import click
# from rich.console import Console
# from rich.panel import Panel
# from rich.table import Table
# from rich import box

# from docgen.analyzer import analyze_code, analyze_folder
# from docgen.coverage import generate_coverage_report, generate_folder_coverage
# from docgen.generator import generate_docstrings, insert_docstrings_into_source
# from docgen.validator import validate_pep257, validate_folder
# from docgen.configloader import load_project_config

# console = Console()


# # ---------------------------------------------------------------------------
# # Shared options
# # ---------------------------------------------------------------------------

# def _style_option(default: str = "google"):
#     return click.option(
#         "--style", "-s",
#         type=click.Choice(["google", "numpy", "rest", "pep257"], case_sensitive=False),
#         default=default,
#         show_default=True,
#         help="Docstring style to generate.",
#     )


# def _recursive_option():
#     return click.option("--recursive/--no-recursive", "-r/ ", default=True, show_default=True,
#                         help="Recurse into sub-directories.")


# def _json_option():
#     return click.option("--json", "output_json", is_flag=True, default=False,
#                         help="Output results as JSON.")


# def _ignore_option():
#     return click.option("--ignore", default="", help="Comma-separated pydocstyle codes to ignore.")


# # ---------------------------------------------------------------------------
# # CLI group
# # ---------------------------------------------------------------------------

# @click.group()
# @click.version_option(package_name="docgen")
# def main() -> None:
#     """docgen — Automated Python Docstring Generator, Validator & Coverage Suite."""


# # ---------------------------------------------------------------------------
# # analyze
# # ---------------------------------------------------------------------------

# @main.command()
# @click.argument("target")
# @_recursive_option()
# @_json_option()
# def analyze(target: str, recursive: bool, output_json: bool) -> None:
#     """Analyze TARGET (file or directory) and print AST metadata."""
#     cfg = load_project_config()
#     path = Path(target)

#     if path.is_file():
#         modules = [analyze_code(path)]
#     elif path.is_dir():
#         modules = analyze_folder(path, recursive=recursive, include_private=cfg.include_private)
#     else:
#         console.print(f"[red]Error:[/red] '{target}' not found.")
#         sys.exit(1)

#     if output_json:
#         result = []
#         for m in modules:
#             result.append({
#                 "filepath": m.filepath,
#                 "syntax_error": m.syntax_error,
#                 "has_module_docstring": m.has_module_docstring,
#                 "functions": [f.qualified_name for f in m.functions],
#                 "classes": [c.name for c in m.classes],
#             })
#         click.echo(json.dumps(result, indent=2))
#         return

#     for m in modules:
#         console.rule(f"[bold cyan]{m.filepath}")
#         if m.syntax_error:
#             console.print(f"[red]⚠ Syntax error:[/red] {m.syntax_error}")
#             continue

#         table = Table(box=box.SIMPLE_HEAD, show_header=True)
#         table.add_column("Name", style="bold")
#         table.add_column("Kind")
#         table.add_column("Documented", justify="center")
#         table.add_column("Line", justify="right")

#         for func in m.functions:
#             documented = "✅" if func.has_docstring else "❌"
#             table.add_row(func.name, func.kind, documented, str(func.lineno))

#         for cls in m.classes:
#             documented = "✅" if cls.has_docstring else "❌"
#             table.add_row(cls.name, "class", documented, str(cls.lineno))
#             for method in cls.methods:
#                 documented = "✅" if method.has_docstring else "❌"
#                 table.add_row(f"  {method.qualified_name}", method.kind, documented, str(method.lineno))

#         console.print(table)


# # ---------------------------------------------------------------------------
# # coverage
# # ---------------------------------------------------------------------------

# @main.command()
# @click.argument("target")
# @_recursive_option()
# @_json_option()
# @click.option("--fail-under", type=float, default=None,
#               help="Exit 1 if coverage is below this percentage.")
# def coverage(target: str, recursive: bool, output_json: bool, fail_under: Optional[float]) -> None:
#     """Show docstring coverage for TARGET (file or directory)."""
#     cfg = load_project_config()
#     threshold = fail_under if fail_under is not None else cfg.fail_under
#     path = Path(target)

#     if path.is_file():
#         report = generate_coverage_report(path, include_private=cfg.include_private)
#         reports = [report]
#         total_pct = report.coverage_pct
#     elif path.is_dir():
#         proj = generate_folder_coverage(path, recursive=recursive, include_private=cfg.include_private)
#         reports = proj.files
#         total_pct = proj.coverage_pct
#     else:
#         console.print(f"[red]Error:[/red] '{target}' not found.")
#         sys.exit(1)

#     if output_json:
#         if path.is_file():
#             click.echo(reports[0].to_dict().__str__())
#         else:
#             from docgen.coverage import generate_folder_coverage
#             proj2 = generate_folder_coverage(path, recursive=recursive)
#             click.echo(proj2.to_json())
#         return

#     for r in reports:
#         color = "green" if r.coverage_pct >= threshold else "red"
#         console.print(Panel(
#             f"[bold]{r.filepath}[/bold]\n"
#             f"  Total: {r.total_objects}  |  "
#             f"Documented: [green]{r.documented}[/green]  |  "
#             f"Missing: [red]{r.undocumented}[/red]  |  "
#             f"Coverage: [{color}]{r.coverage_pct:.1f}%[/{color}]",
#             expand=False,
#         ))

#         if r.undocumented:
#             undoc_table = Table(box=box.MINIMAL, show_header=False)
#             for obj in r.objects:
#                 if not obj.has_docstring:
#                     undoc_table.add_row(f"  [yellow]⚠[/yellow] {obj.qualified_name}", obj.kind)
#             console.print(undoc_table)

#     console.rule()
#     color = "green" if total_pct >= threshold else "red"
#     console.print(f"Overall coverage: [{color}]{total_pct:.1f}%[/{color}]  (threshold: {threshold:.0f}%)")

#     if total_pct < threshold:
#         console.print(f"[red]✗ Coverage {total_pct:.1f}% is below the required {threshold:.0f}%.[/red]")
#         sys.exit(1)


# # ---------------------------------------------------------------------------
# # validate
# # ---------------------------------------------------------------------------

# @main.command()
# @click.argument("target")
# @_recursive_option()
# @_ignore_option()
# @_json_option()
# def validate(target: str, recursive: bool, ignore: str, output_json: bool) -> None:
#     """Run PEP 257 validation on TARGET (file or directory)."""
#     ignore_codes = [c.strip() for c in ignore.split(",") if c.strip()]
#     cfg = load_project_config()
#     all_ignores = list(set(ignore_codes + cfg.ignore))

#     path = Path(target)
#     if path.is_file():
#         reports = [validate_pep257(path, ignore_codes=all_ignores or None)]
#     elif path.is_dir():
#         reports = validate_folder(path, recursive=recursive, ignore_codes=all_ignores or None)
#     else:
#         console.print(f"[red]Error:[/red] '{target}' not found.")
#         sys.exit(1)

#     if output_json:
#         out = []
#         for r in reports:
#             out.append({
#                 "filepath": r.filepath,
#                 "total": r.total,
#                 "violations": [{"code": v.code, "lineno": v.lineno, "message": v.message,
#                                  "severity": v.severity} for v in r.violations],
#             })
#         click.echo(json.dumps(out, indent=2))
#         return

#     total_violations = 0
#     for r in reports:
#         if not r.pydocstyle_available:
#             console.print(f"[yellow]pydocstyle not available:[/yellow] {r.error_message}")
#             continue
#         if not r.violations:
#             console.print(f"[green]✅ {r.filepath}[/green] — no violations")
#             continue

#         console.rule(f"[bold]{r.filepath}[/bold]  ({r.total} violations)")
#         for v in r.violations:
#             color = "red" if v.severity == "error" else "yellow"
#             console.print(f"  [{color}]{v.code}[/{color}] L{v.lineno}  {v.message}")
#         total_violations += r.total

#     if total_violations:
#         console.print(f"\n[red]Total violations: {total_violations}[/red]")
#         sys.exit(1)


# # ---------------------------------------------------------------------------
# # generate
# # ---------------------------------------------------------------------------

# @main.command()
# @click.argument("filepath")
# @_style_option()
# @click.option("--output", "-o", default=None, help="Write patched file to this path.")
# @click.option("--dry-run", is_flag=True, help="Print diff without writing.")
# @click.option("--skip-existing/--overwrite", default=True, show_default=True,
#               help="Skip already-documented objects.")
# def generate(filepath: str, style: str, output: Optional[str], dry_run: bool, skip_existing: bool) -> None:
#     """Generate and insert docstrings into FILEPATH."""
#     path = Path(filepath)
#     if not path.exists():
#         console.print(f"[red]Error:[/red] '{filepath}' not found.")
#         sys.exit(1)

#     source = path.read_text(encoding="utf-8")
#     from docgen.analyzer import analyze_code as _ac
#     module = _ac(path)

#     if module.syntax_error:
#         console.print(f"[red]Syntax error:[/red] {module.syntax_error}")
#         sys.exit(1)

#     patched = insert_docstrings_into_source(source, module, style=style, skip_existing=skip_existing)

#     if dry_run:
#         import difflib
#         diff = difflib.unified_diff(
#             source.splitlines(keepends=True),
#             patched.splitlines(keepends=True),
#             fromfile=f"a/{path.name}",
#             tofile=f"b/{path.name}",
#         )
#         click.echo("".join(diff))
#         return

#     dest = Path(output) if output else path
#     dest.write_text(patched, encoding="utf-8")
#     console.print(f"[green]✅ Written:[/green] {dest}")


# # ---------------------------------------------------------------------------
# # report  (combined analyze + coverage + validate)
# # ---------------------------------------------------------------------------

# @main.command()
# @click.argument("target")
# @_recursive_option()
# @_style_option()
# @_ignore_option()
# @_json_option()
# def report(target: str, recursive: bool, style: str, ignore: str, output_json: bool) -> None:
#     """Full combined report: analysis + coverage + PEP 257 validation."""
#     ignore_codes = [c.strip() for c in ignore.split(",") if c.strip()]
#     cfg = load_project_config()
#     path = Path(target)

#     if path.is_file():
#         modules = [analyze_code(path)]
#         cov = generate_coverage_report(path)
#         val_reports = [validate_pep257(path, ignore_codes=ignore_codes or None)]
#     elif path.is_dir():
#         modules = analyze_folder(path, recursive=recursive)
#         from docgen.coverage import generate_folder_coverage
#         proj = generate_folder_coverage(path, recursive=recursive)
#         cov = proj  # type: ignore[assignment]
#         val_reports = validate_folder(path, recursive=recursive, ignore_codes=ignore_codes or None)
#     else:
#         console.print(f"[red]Error:[/red] '{target}' not found.")
#         sys.exit(1)

#     if output_json:
#         result = {
#             "coverage": cov.to_dict() if hasattr(cov, "to_dict") else {},
#             "violations": [
#                 {"filepath": r.filepath, "total": r.total,
#                  "violations": [{"code": v.code, "lineno": v.lineno, "message": v.message} for v in r.violations]}
#                 for r in val_reports
#             ],
#         }
#         click.echo(json.dumps(result, indent=2))
#         return

#     console.print(Panel("[bold blue]docgen Full Report[/bold blue]", expand=False))

#     # Coverage summary
#     if hasattr(cov, "coverage_pct"):
#         color = "green" if cov.coverage_pct >= cfg.fail_under else "red"
#         console.print(f"\n[bold]Coverage:[/bold] [{color}]{cov.coverage_pct:.1f}%[/{color}]")

#     # Validation summary
#     total_v = sum(r.total for r in val_reports)
#     console.print(f"[bold]PEP 257 violations:[/bold] {'[red]' + str(total_v) + '[/red]' if total_v else '[green]0[/green]'}")


# # ---------------------------------------------------------------------------
# # scan  (alias for analyze with folder focus)
# # ---------------------------------------------------------------------------

# @main.command()
# @click.argument("folder")
# @_recursive_option()
# @_json_option()
# def scan(folder: str, recursive: bool, output_json: bool) -> None:
#     """Scan FOLDER and list all undocumented objects."""
#     ctx = click.get_current_context()
#     ctx.invoke(analyze, target=folder, recursive=recursive, output_json=output_json)


# # ---------------------------------------------------------------------------
# # ui
# # ---------------------------------------------------------------------------

# @main.command()
# @click.option("--port", default=8501, show_default=True, help="Streamlit server port.")
# def ui(port: int) -> None:
#     """Launch the interactive Streamlit dashboard."""
#     import importlib
#     import subprocess

#     uiapp = importlib.util.find_spec("docgen.uiapp")
#     if uiapp is None:
#         console.print("[red]Could not locate docgen.uiapp module.[/red]")
#         sys.exit(1)

#     module_file = uiapp.origin
#     console.print(f"[green]Launching Streamlit UI on port {port}…[/green]")
#     subprocess.run([sys.executable, "-m", "streamlit", "run", module_file,
#                     "--server.port", str(port)], check=False)



"""Command-line interface for docgen.

Usage examples::

    docgen analyze src/
    docgen coverage src/ --recursive
    docgen validate src/my_module.py --ignore D100,D104
    docgen generate src/my_module.py --style numpy --output out.py
    docgen report src/ --json
    docgen scan src/ --recursive
    docgen ui
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from docgen.analyzer import analyze_code, analyze_folder
from docgen.coverage import generate_coverage_report, generate_folder_coverage
from docgen.generator import generate_docstrings, insert_docstrings_into_source
from docgen.validator import validate_pep257, validate_folder
from docgen.configloader import load_project_config

console = Console()


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

def _style_option(default: str = "google"):
    return click.option(
        "--style", "-s",
        type=click.Choice(["google", "numpy", "rest", "pep257"], case_sensitive=False),
        default=default,
        show_default=True,
        help="Docstring style to generate.",
    )


def _recursive_option():
    return click.option("--recursive/--no-recursive", "-r/ ", default=True, show_default=True,
                        help="Recurse into sub-directories.")


def _json_option():
    return click.option("--json", "output_json", is_flag=True, default=False,
                        help="Output results as JSON.")


def _ignore_option():
    return click.option("--ignore", default="", help="Comma-separated pydocstyle codes to ignore.")


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="docgen")
def main() -> None:
    """docgen — Automated Python Docstring Generator, Validator & Coverage Suite."""


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

@main.command()
@click.argument("target")
@_recursive_option()
@_json_option()
def analyze(target: str, recursive: bool, output_json: bool) -> None:
    """Analyze TARGET (file or directory) and print AST metadata."""
    cfg = load_project_config()
    path = Path(target)

    if path.is_file():
        modules = [analyze_code(path)]
    elif path.is_dir():
        modules = analyze_folder(path, recursive=recursive, include_private=cfg.include_private)
    else:
        console.print(f"[red]Error:[/red] '{target}' not found.")
        sys.exit(1)

    if output_json:
        result = []
        for m in modules:
            result.append({
                "filepath": m.filepath,
                "syntax_error": m.syntax_error,
                "has_module_docstring": m.has_module_docstring,
                "functions": [f.qualified_name for f in m.functions],
                "classes": [c.name for c in m.classes],
            })
        click.echo(json.dumps(result, indent=2))
        return

    for m in modules:
        if m.syntax_error:
            console.print(f"[red]❌ {m.filepath} — Syntax error: {m.syntax_error}[/red]")
            continue
        total = len(m.functions) + sum(len(c.methods) for c in m.classes)
        documented = sum(1 for f in m.functions if f.has_docstring) + \
                     sum(1 for c in m.classes for meth in c.methods if meth.has_docstring)
        pct = (documented / total * 100) if total else 100.0
        color = "green" if pct == 100.0 else "yellow" if pct >= 80 else "red"
        status = "✅ PERFECT" if pct == 100.0 else "⚠ INCOMPLETE"
        console.print(f"[bold]{Path(m.filepath).name}[/bold]  [{color}]{pct:.1f}%[/{color}]  {status}")


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------

@main.command()
@click.argument("target")
@_recursive_option()
@_json_option()
@click.option("--fail-under", type=float, default=None,
              help="Exit 1 if coverage is below this percentage.")
def coverage(target: str, recursive: bool, output_json: bool, fail_under: Optional[float]) -> None:
    """Show docstring coverage for TARGET (file or directory)."""
    cfg = load_project_config()
    threshold = fail_under if fail_under is not None else cfg.fail_under
    path = Path(target)

    if path.is_file():
        report = generate_coverage_report(path, include_private=cfg.include_private)
        reports = [report]
        total_pct = report.coverage_pct
    elif path.is_dir():
        proj = generate_folder_coverage(path, recursive=recursive, include_private=cfg.include_private)
        reports = proj.files
        total_pct = proj.coverage_pct
    else:
        console.print(f"[red]Error:[/red] '{target}' not found.")
        sys.exit(1)

    if output_json:
        if path.is_file():
            click.echo(reports[0].to_dict().__str__())
        else:
            from docgen.coverage import generate_folder_coverage
            proj2 = generate_folder_coverage(path, recursive=recursive)
            click.echo(proj2.to_json())
        return

    color = "green" if total_pct >= threshold else "red"
    status = "✅ PASSED" if total_pct >= threshold else "❌ FAILED"
    console.print(f"Coverage: [{color}]{total_pct:.1f}%[/{color}]  [{color}]{status}[/{color}]")

    if total_pct < threshold:
        sys.exit(1)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

@main.command()
@click.argument("target")
@_recursive_option()
@_ignore_option()
@_json_option()
def validate(target: str, recursive: bool, ignore: str, output_json: bool) -> None:
    """Run PEP 257 validation on TARGET (file or directory)."""
    ignore_codes = [c.strip() for c in ignore.split(",") if c.strip()]
    cfg = load_project_config()
    all_ignores = list(set(ignore_codes + cfg.ignore))

    path = Path(target)
    if path.is_file():
        reports = [validate_pep257(path, ignore_codes=all_ignores or None)]
    elif path.is_dir():
        reports = validate_folder(path, recursive=recursive, ignore_codes=all_ignores or None)
    else:
        console.print(f"[red]Error:[/red] '{target}' not found.")
        sys.exit(1)

    if output_json:
        out = []
        for r in reports:
            out.append({
                "filepath": r.filepath,
                "total": r.total,
                "violations": [{"code": v.code, "lineno": v.lineno, "message": v.message,
                                 "severity": v.severity} for v in r.violations],
            })
        click.echo(json.dumps(out, indent=2))
        return

    total_violations = sum(r.total for r in reports)
    total_checks = sum(1 for r in reports if r.pydocstyle_available)

    if any(not r.pydocstyle_available for r in reports):
        console.print(f"[yellow]⚠ pydocstyle not available[/yellow]")
        return

    if total_violations == 0:
        console.print(f"[green]✅ PASSED  —  PEP 257: 100%  (0 violations)[/green]")
    else:
        console.print(f"[red]❌ FAILED  —  PEP 257: {total_violations} violation(s) found[/red]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

@main.command()
@click.argument("filepath")
@_style_option()
@click.option("--output", "-o", default=None, help="Write patched file to this path.")
@click.option("--dry-run", is_flag=True, help="Print diff without writing.")
@click.option("--skip-existing/--overwrite", default=True, show_default=True,
              help="Skip already-documented objects.")
def generate(filepath: str, style: str, output: Optional[str], dry_run: bool, skip_existing: bool) -> None:
    """Generate and insert docstrings into FILEPATH."""
    path = Path(filepath)
    if not path.exists():
        console.print(f"[red]Error:[/red] '{filepath}' not found.")
        sys.exit(1)

    source = path.read_text(encoding="utf-8")
    from docgen.analyzer import analyze_code as _ac
    module = _ac(path)

    if module.syntax_error:
        console.print(f"[red]Syntax error:[/red] {module.syntax_error}")
        sys.exit(1)

    patched = insert_docstrings_into_source(source, module, style=style, skip_existing=skip_existing)

    if dry_run:
        import difflib
        diff = difflib.unified_diff(
            source.splitlines(keepends=True),
            patched.splitlines(keepends=True),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
        )
        click.echo("".join(diff))
        return

    dest = Path(output) if output else path
    dest.write_text(patched, encoding="utf-8")
    console.print(f"[green]✅ Written:[/green] {dest}")


# ---------------------------------------------------------------------------
# report  (combined analyze + coverage + validate)
# ---------------------------------------------------------------------------

@main.command()
@click.argument("target")
@_recursive_option()
@_style_option()
@_ignore_option()
@_json_option()
def report(target: str, recursive: bool, style: str, ignore: str, output_json: bool) -> None:
    """Full combined report: analysis + coverage + PEP 257 validation."""
    ignore_codes = [c.strip() for c in ignore.split(",") if c.strip()]
    cfg = load_project_config()
    path = Path(target)

    if path.is_file():
        modules = [analyze_code(path)]
        cov = generate_coverage_report(path)
        val_reports = [validate_pep257(path, ignore_codes=ignore_codes or None)]
    elif path.is_dir():
        modules = analyze_folder(path, recursive=recursive)
        from docgen.coverage import generate_folder_coverage
        proj = generate_folder_coverage(path, recursive=recursive)
        cov = proj  # type: ignore[assignment]
        val_reports = validate_folder(path, recursive=recursive, ignore_codes=ignore_codes or None)
    else:
        console.print(f"[red]Error:[/red] '{target}' not found.")
        sys.exit(1)

    if output_json:
        result = {
            "coverage": cov.to_dict() if hasattr(cov, "to_dict") else {},
            "violations": [
                {"filepath": r.filepath, "total": r.total,
                 "violations": [{"code": v.code, "lineno": v.lineno, "message": v.message} for v in r.violations]}
                for r in val_reports
            ],
        }
        click.echo(json.dumps(result, indent=2))
        return

    total_v = sum(r.total for r in val_reports)
    cov_pct = cov.coverage_pct if hasattr(cov, "coverage_pct") else 0.0
    cov_color = "green" if cov_pct >= cfg.fail_under else "red"
    val_status = "[green]✅ PASSED[/green]" if total_v == 0 else f"[red]❌ {total_v} violation(s)[/red]"
    cov_status = "[green]✅ PASSED[/green]" if cov_pct >= cfg.fail_under else "[red]❌ FAILED[/red]"

    console.print(f"Coverage:    [{cov_color}]{cov_pct:.1f}%[/{cov_color}]  {cov_status}")
    console.print(f"PEP 257:     {val_status}")


# ---------------------------------------------------------------------------
# scan  (alias for analyze with folder focus)
# ---------------------------------------------------------------------------

@main.command()
@click.argument("folder")
@_recursive_option()
@_json_option()
def scan(folder: str, recursive: bool, output_json: bool) -> None:
    """Scan FOLDER and list all undocumented objects."""
    ctx = click.get_current_context()
    ctx.invoke(analyze, target=folder, recursive=recursive, output_json=output_json)


# ---------------------------------------------------------------------------
# ui
# ---------------------------------------------------------------------------

@main.command()
@click.option("--port", default=8501, show_default=True, help="Streamlit server port.")
def ui(port: int) -> None:
    """Launch the interactive Streamlit dashboard."""
    import importlib
    import subprocess

    uiapp = importlib.util.find_spec("docgen.uiapp")
    if uiapp is None:
        console.print("[red]Could not locate docgen.uiapp module.[/red]")
        sys.exit(1)

    module_file = uiapp.origin
    console.print(f"[green]Launching Streamlit UI on port {port}…[/green]")
    subprocess.run([sys.executable, "-m", "streamlit", "run", module_file,
                    "--server.port", str(port)], check=False)
