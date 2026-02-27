"""Streamlit interactive dashboard for docgen.

Launch with::

    docgen ui
    # or directly:
    streamlit run src/docgen/uiapp.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import List

import streamlit as st

from docgen.analyzer import ModuleInfo, analyze_code
from docgen.configloader import load_project_config
from docgen.coverage import generate_coverage_report
from docgen.generator import generate_docstrings, insert_docstrings_into_source
from docgen.validator import validate_pep257


# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="docgen — Docstring Suite",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TOOLTIP_PARAMS = "Function parameters extracted from the signature, including type hints and defaults."
_TOOLTIP_RETURNS = "Return type annotation inferred from the function signature."
_TOOLTIP_COVERAGE = "Percentage of classes, functions, and methods that have docstrings."
_TOOLTIP_PEP257 = "PEP 257 defines conventions for Python docstrings (https://peps.python.org/pep-0257/)."
_TOOLTIP_STYLE = "Select the docstring format that matches your project's coding standards."


def _severity_badge(severity: str) -> str:
    return "🔴" if severity == "error" else "🟡"


def _coverage_color(pct: float) -> str:
    if pct >= 80:
        return "green"
    if pct >= 50:
        return "orange"
    return "red"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar() -> dict:
    st.sidebar.title("⚙️ Settings")

    cfg = load_project_config()

    style = st.sidebar.selectbox(
        "Docstring style",
        ["google", "numpy", "rest", "pep257"],
        index=["google", "numpy", "rest", "pep257"].index(cfg.style),
        help=_TOOLTIP_STYLE,
    )

    fail_under = st.sidebar.slider(
        "Coverage threshold (%)",
        min_value=0,
        max_value=100,
        value=int(cfg.fail_under),
        step=5,
        help="Minimum acceptable coverage percentage.",
    )

    ignore_raw = st.sidebar.text_input(
        "Ignore PEP 257 codes",
        value=", ".join(cfg.ignore),
        placeholder="e.g. D100, D104",
        help="Comma-separated codes to suppress during validation.",
    )
    ignore_codes = [c.strip() for c in ignore_raw.split(",") if c.strip()]

    include_private = st.sidebar.checkbox(
        "Include private objects",
        value=cfg.include_private,
        help="Include functions/classes whose names start with _.",
    )

    skip_existing = st.sidebar.checkbox(
        "Skip already documented",
        value=True,
        help="Don't regenerate docstrings for objects that already have them.",
    )

    st.sidebar.markdown("---")

    # Filters
    st.sidebar.subheader("🔍 Filters")
    show_only = st.sidebar.multiselect(
        "Show only",
        options=["Functions", "Classes", "Missing docstrings", "Has docstrings",
                 "PEP 257 errors", "PEP 257 warnings"],
        default=[],
    )

    search_query = st.sidebar.text_input("🔎 Search by name", placeholder="e.g. my_func")

    return {
        "style": style,
        "fail_under": fail_under,
        "ignore_codes": ignore_codes,
        "include_private": include_private,
        "skip_existing": skip_existing,
        "show_only": show_only,
        "search_query": search_query.strip().lower(),
    }


# ---------------------------------------------------------------------------
# Coverage tab
# ---------------------------------------------------------------------------

def _render_coverage(module: ModuleInfo, settings: dict) -> None:
    report = generate_coverage_report(module.filepath or "<string>", include_private=settings["include_private"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Objects", report.total_objects, help=_TOOLTIP_COVERAGE)
    col2.metric("Documented", report.documented)
    col3.metric("Missing", report.undocumented)
    color = _coverage_color(report.coverage_pct)
    col4.markdown(
        f"**Coverage**  \n<span style='font-size:2rem;color:{color}'>{report.coverage_pct:.1f}%</span>",
        unsafe_allow_html=True,
    )

    threshold = settings["fail_under"]
    if report.coverage_pct >= threshold:
        st.success(f"✅ Coverage meets the {threshold}% threshold.")
    else:
        st.error(f"❌ Coverage {report.coverage_pct:.1f}% is below the {threshold}% threshold.")

    # Per-object table
    search = settings["search_query"]
    show_only = settings["show_only"]

    rows = []
    for obj in report.objects:
        if search and search not in obj.name.lower():
            continue
        if "Functions" in show_only and "function" not in obj.kind:
            continue
        if "Classes" in show_only and obj.kind != "class":
            continue
        if "Missing docstrings" in show_only and obj.has_docstring:
            continue
        if "Has docstrings" in show_only and not obj.has_docstring:
            continue
        rows.append(obj)

    if rows:
        st.subheader("Object Coverage")
        header = st.columns([3, 2, 1, 1])
        header[0].markdown("**Name**")
        header[1].markdown("**Kind**")
        header[2].markdown("**Documented**")
        header[3].markdown("**Line**")
        for obj in rows:
            cols = st.columns([3, 2, 1, 1])
            cols[0].code(obj.qualified_name)
            cols[1].write(obj.kind)
            cols[2].write("✅" if obj.has_docstring else "❌")
            cols[3].write(str(obj.lineno) if obj.lineno else "—")

    # JSON export
    with st.expander("📤 Export JSON"):
        st.json(report.to_dict())


# ---------------------------------------------------------------------------
# PEP 257 tab
# ---------------------------------------------------------------------------

def _render_validation(module: ModuleInfo, settings: dict) -> None:
    if not module.filepath or module.filepath == "<string>":
        st.info("Upload a file to run PEP 257 validation.")
        return

    report = validate_pep257(
        Path(module.filepath),
        ignore_codes=settings["ignore_codes"] or None,
    )

    if not report.pydocstyle_available:
        st.warning(f"⚠️ {report.error_message}")
        return

    search = settings["search_query"]
    show_only = settings["show_only"]

    if not report.violations:
        st.success("✅ No PEP 257 violations found!")
        return

    errors_count = len(report.errors)
    warnings_count = len(report.warnings)
    c1, c2 = st.columns(2)
    c1.metric("Errors", errors_count, help=_TOOLTIP_PEP257)
    c2.metric("Warnings", warnings_count)

    for v in report.violations:
        if search and search not in v.object_name.lower() and search not in v.message.lower():
            continue
        if "PEP 257 errors" in show_only and v.severity != "error":
            continue
        if "PEP 257 warnings" in show_only and v.severity != "warning":
            continue
        badge = _severity_badge(v.severity)
        with st.expander(f"{badge} [{v.code}] Line {v.lineno}  —  {v.object_name}"):
            st.write(f"**Message:** {v.message}")
            st.write(f"**Severity:** {v.severity.capitalize()}")
            st.write(f"**Code:** `{v.code}` · [pydocstyle docs](http://www.pydocstyle.org/en/stable/error_codes.html)")


# ---------------------------------------------------------------------------
# Generator tab
# ---------------------------------------------------------------------------

def _render_generator(module: ModuleInfo, source: str, settings: dict) -> None:
    if module.syntax_error:
        st.error(f"Cannot generate docstrings: {module.syntax_error}")
        return

    generated_map = generate_docstrings(
        module,
        style=settings["style"],
        skip_existing=settings["skip_existing"],
        include_private=settings["include_private"],
    )

    if not generated_map:
        st.success("🎉 All objects are already documented!")
        return

    st.info(f"Generated {len(generated_map)} docstring(s) using **{settings['style']}** style.")

    search = settings["search_query"]
    for name, docstring in generated_map.items():
        if search and search not in name.lower():
            continue
        with st.expander(f"📄 `{name}`"):
            st.code(docstring, language="python")

    st.markdown("---")
    st.subheader("📝 Patched Source Preview")
    patched = insert_docstrings_into_source(
        source,
        module,
        style=settings["style"],
        skip_existing=settings["skip_existing"],
    )
    st.code(patched, language="python")

    st.download_button(
        label="⬇️ Download patched file",
        data=patched,
        file_name=Path(module.filepath or "patched.py").name,
        mime="text/plain",
    )


# ---------------------------------------------------------------------------
# Existing docstrings tab
# ---------------------------------------------------------------------------

def _render_existing(module: ModuleInfo, settings: dict) -> None:
    search = settings["search_query"]

    def _show_func(func):
        if search and search not in func.name.lower():
            return
        if func.has_docstring:
            with st.expander(f"📘 `{func.qualified_name}` ({func.kind})"):
                st.code(func.existing_docstring, language="text")
                if func.params:
                    st.caption(
                        f"**Params:** {', '.join(p.name for p in func.params)}"
                        + (f" | **Returns:** `{func.return_annotation}`" if func.return_annotation else ""),
                    )

    for func in module.functions:
        _show_func(func)
    for cls in module.classes:
        if cls.has_docstring and (not search or search in cls.name.lower()):
            with st.expander(f"🏛️ `{cls.name}` (class)"):
                st.code(cls.existing_docstring, language="text")
        for method in cls.methods:
            _show_func(method)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Streamlit docgen dashboard."""
    st.title("📝 docgen — Docstring Generator & Validator")
    st.caption("Automated Python docstring generation, PEP 257 validation, and coverage analysis.")

    settings = _render_sidebar()

    # File upload
    st.subheader("Upload Python file(s)")
    uploaded = st.file_uploader(
        "Drop one or more .py files",
        type=["py"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if not uploaded:
        st.info("👆 Upload a Python file to get started.")
        st.markdown("""
        **Features:**
        - 🔍 AST-based code analysis
        - 📝 Docstring generation (Google, NumPy, reST, PEP 257)
        - 📊 Coverage reporting
        - ✅ PEP 257 validation
        - ⬇️ Download patched files
        """)
        return

    # File selector when multiple uploaded
    if len(uploaded) > 1:
        selected_name = st.selectbox("Select file", [f.name for f in uploaded])
        file_obj = next(f for f in uploaded if f.name == selected_name)
    else:
        file_obj = uploaded[0]

    source = file_obj.read().decode("utf-8")

    # Write to temp file so pydocstyle can read it
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False,
                                     encoding="utf-8", prefix=file_obj.name + "_") as tmp:
        tmp.write(source)
        tmp_path = tmp.name

    module = analyze_code(source, filepath=tmp_path)

    if module.syntax_error:
        st.error(f"⚠️ Syntax error in `{file_obj.name}`: {module.syntax_error}")
        return

    # Stats banner
    funcs_total = len(module.functions) + sum(len(c.methods) for c in module.classes)
    st.success(
        f"Parsed **{file_obj.name}** — "
        f"{len(module.classes)} class(es), {funcs_total} function(s)/method(s)"
    )

    # Main tabs
    tab_cov, tab_gen, tab_val, tab_exist = st.tabs([
        "📊 Coverage", "🛠️ Generate", "✅ PEP 257 Validate", "📖 Existing Docstrings"
    ])

    with tab_cov:
        _render_coverage(module, settings)

    with tab_gen:
        _render_generator(module, source, settings)

    with tab_val:
        _render_validation(module, settings)

    with tab_exist:
        _render_existing(module, settings)

    # Cleanup temp file
    try:
        Path(tmp_path).unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
