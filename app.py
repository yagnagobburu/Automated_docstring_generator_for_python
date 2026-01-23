import streamlit as st
from parser_code import (
    analyze_code,
    generate_docstring,
    generate_cover_report,
    validate_with_pydocstyle,
)

st.set_page_config(page_title="Automated Docstring Generator", layout="wide")
st.title("📄 Automated Python Docstring Generator & Coverage Report")

uploaded_file = st.file_uploader("Upload a Python (.py) file", type=["py"])

if uploaded_file:
    st.subheader("⚙️ Documentation Options")

    doc_style = st.selectbox(
        "Select Docstring Style",
        ["Google", "NumPy", "reST"]
    )

    if st.button("🔍 Analyze Code"):
        source_code = uploaded_file.read().decode("utf-8")

        analysis = analyze_code(source_code)
        report = generate_cover_report(analysis)
        validation = validate_with_pydocstyle(uploaded_file.name)

        # ---------- Coverage Summary ----------
        st.subheader("📊 Coverage Summary")

        total_items = report["total_classes"] + report["total_functions"]
        documented_items = (
            len(report["classes_with_docstrings"]) +
            len(report["functions_with_docstrings"])
        )

        coverage_percent = (
            (documented_items / total_items) * 100 if total_items else 0
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Elements", total_items)
        col2.metric("Documented", documented_items)
        col3.metric("Coverage %", f"{coverage_percent:.2f}%")

        # ---------- Detailed Coverage ----------
        st.subheader("🧱 Existing Docstring Coverage")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### ✅ With Docstrings")
            st.write({
                "Classes": report["classes_with_docstrings"],
                "Functions": report["functions_with_docstrings"],
            })

        with col2:
            st.markdown("#### ❌ Without Docstrings")
            st.write({
                "Classes": report["classes_without_docstrings"],
                "Functions": report["functions_without_docstrings"],
            })

        # ---------- Generated Docstrings ----------
        st.subheader("🧱 Generated Docstrings")

        for cls in analysis["classes"]:
            st.code(generate_docstring(cls, doc_style, True), "python")

        for fn in analysis["functions"]:
            st.code(generate_docstring(fn, doc_style), "python")

        # ---------- Compliance Report ----------
        st.subheader("🧪 PEP-257 Compliance Report")

        violations = validation["total_issues"]

        if violations == 0:
            compliance_percent = 100
        else:
            compliance_percent = max(0, 100 - (violations * 10))

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Violations", violations)
        col2.metric(
            "Compliance Status",
            "✅ PASS" if validation["is_valid"] else "❌ FAIL"
        )
        col3.metric("Compliance %", f"{compliance_percent}%")

        if validation["issues"]:
            st.markdown("### ❌ Violations")
            for v in validation["issues"]:
                st.write(
                    f"**{v['code']}** | {v['object']} | "
                    f"Line {v['line']} – {v['message']}"
                )
        else:
            st.success("No PEP-257 violations found 🎉")
