import ast
from typing import Dict, List
import pydocstyle


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes: List[Dict] = []
        self.functions: List[Dict] = []

    def visit_ClassDef(self, node):
        self.classes.append({
            "name": node.name,
            "has_docstring": ast.get_docstring(node) is not None,
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        fn_info = {
            "name": node.name,
            "params": [arg.arg for arg in node.args.args if arg.arg != "self"],
            "returns": "None",
            "has_docstring": ast.get_docstring(node) is not None,
        }

        for n in ast.walk(node):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Name):
                fn_info["returns"] = n.value.id

        self.functions.append(fn_info)
        self.generic_visit(node)


def analyze_code(source: str) -> Dict:
    tree = ast.parse(source)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return {
        "classes": analyzer.classes,
        "functions": analyzer.functions,
    }


# ---------- Docstring Generators ----------

def generate_google_docstring(item: Dict, is_class=False) -> str:
    doc = f'''"""
{item["name"]}

'''
    if not is_class:
        doc += "Args:\n"
        for p in item.get("params", []):
            doc += f"    {p}: description\n"
        doc += f"\nReturns:\n    {item.get('returns', 'None')}\n"
    doc += '"""'
    return doc


def generate_numpy_docstring(item: Dict, is_class=False) -> str:
    doc = f'''"""
{item["name"]}

'''
    if not is_class:
        doc += "Parameters\n----------\n"
        for p in item.get("params", []):
            doc += f"{p}\n    description\n"
        doc += "\nReturns\n-------\n"
        doc += f"{item.get('returns', 'None')}\n"
    doc += '"""'
    return doc


def generate_rest_docstring(item: Dict, is_class=False) -> str:
    doc = f'''"""
{item["name"]}

'''
    if not is_class:
        for p in item.get("params", []):
            doc += f":param {p}: description\n"
        doc += f":return: {item.get('returns', 'None')}\n"
    doc += '"""'
    return doc


def generate_docstring(item: Dict, style="Google", is_class=False) -> str:
    if style == "Google":
        return generate_google_docstring(item, is_class)
    if style == "NumPy":
        return generate_numpy_docstring(item, is_class)
    if style == "reST":
        return generate_rest_docstring(item, is_class)
    return generate_google_docstring(item, is_class)


def generate_cover_report(analysis: Dict) -> Dict:
    return {
        "total_classes": len(analysis["classes"]),
        "total_functions": len(analysis["functions"]),
        "classes_with_docstrings": [
            c["name"] for c in analysis["classes"] if c["has_docstring"]
        ],
        "classes_without_docstrings": [
            c["name"] for c in analysis["classes"] if not c["has_docstring"]
        ],
        "functions_with_docstrings": [
            f["name"] for f in analysis["functions"] if f["has_docstring"]
        ],
        "functions_without_docstrings": [
            f["name"] for f in analysis["functions"] if not f["has_docstring"]
        ],
    }


def validate_with_pydocstyle(file_path: str) -> Dict:
    issues = []
    for error in pydocstyle.check([file_path]):
        issues.append({
            "code": error.code,
            "message": error.message,
            "line": error.line,
            "object": error.definition,
        })

    return {
        "is_valid": len(issues) == 0,
        "total_issues": len(issues),
        "issues": issues,
    }
