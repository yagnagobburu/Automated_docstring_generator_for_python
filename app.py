# app.py
import streamlit as st
from parser import analyze_code, generate_baseline_docstring, generate_cover_report, validate_with_pydocstyle 

st.set_page_config(page_title="Automated Docstring Generator", layout="wide")

st.title("📄 Automated Python Docstring Generator & Coverage Report")

uploaded_file = st.file_uploader("Upload a Python (.py) file", type=["py"])

if uploaded_file:
    source_code = uploaded_file.read().decode("utf-8")
    analysis = analyze_code(source_code)
    report = generate_cover_report(analysis)

    st.subheader("📌 Code Overview")
    st.metric("Docstring Coverage", f"{len(report['functions_with_docstrings']+report['classes_with_docstrings'])} / {report['total_functions']+report['total_classes']}")
    st.divider()

    st.subheader("🧱 Baseline Docstrings")

    st.markdown("### Classes")
    for cls in analysis["classes"]:
        st.code(generate_baseline_docstring(cls, is_class=True), language="python")

        for method in cls["methods"]:
            st.code(method)

    st.markdown("### Functions / Methods")
    for fn in analysis["functions"]:
        st.code(generate_baseline_docstring(fn), language="python")

    st.divider()
    
    st.subheader("📊 Docstring Coverage Report")

# ---- Metrics ----
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Classes", report["total_classes"])

    with col2:
        st.metric("Total Functions", report["total_functions"])

    st.divider()

    # ---- Classes ----
    st.markdown("### 🧱 Classes")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ With Docstrings")
        if report["classes_with_docstrings"]:
            st.write(report["classes_with_docstrings"])
        else:
            st.write("None")

    with col2:
        st.markdown("#### ❌ Without Docstrings")
        if report["classes_without_docstrings"]:
            st.write(report["classes_without_docstrings"])
        else:
            st.write("None")

    st.divider()

    # ---- Functions & Methods ----
    st.markdown("### 🔧 Functions & Methods")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ With Docstrings")
        if report["functions_with_docstrings"]:
            st.write(report["functions_with_docstrings"])
        else:
            st.write("None")

    with col2:
        st.markdown("#### ❌ Without Docstrings")
        if report["functions_without_docstrings"]:
            st.write(report["functions_without_docstrings"])
        else:
            st.write("None")
            
    st.divider()      
            
    st.subheader("🧪 PEP-257 Docstring Validation (pydocstyle)")

    validation = validate_with_pydocstyle(uploaded_file.name)

    st.metric("Total Violations", validation["total_issues"])
    st.metric("Validation Status", "✅ PASS" if validation["is_valid"] else "❌ FAIL")

    if validation["issues"]:
        st.markdown("### ❌ Violations")
        for issue in validation["issues"]:
            st.write(
                f"**{issue['code']}** | {issue['object']} | "
                f"Line {issue['line']} – {issue['message']}"
            )
    else:
        st.success("No PEP-257 violations found 🎉")
