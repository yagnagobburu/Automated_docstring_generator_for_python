
import ast
from typing import Dict

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = []

    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "methods": [],
            "class_variables": [],
            "has_docstring": ast.get_docstring(node) is not None
        }

        for item in node.body:
            if isinstance(item,ast.Assign):
                for target in item.targets:
                    if isinstance(target,ast.Name):
                        class_info["class_variables"].append(target.id)
            if isinstance(item, ast.FunctionDef):
                class_info["methods"].append(self._extract_function(item))

        self.classes.append(class_info)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append(self._extract_function(node))
        self.generic_visit(node)

    def _extract_function(self, node):
        params = [ arg.arg for arg in node.args.args if arg.arg!="self" ]
        variables = set()
        
        for n in ast.walk(node):
            if isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        variables.add(target.id)
            #return values
            if isinstance(n, ast.Return) and n.value:
                if isinstance(n.value, ast.Name):
                    return_value = n.value.id

        return {
            "name": node.name,
            "params": params,
            "returns": return_value,
            "variables": sorted(variables),
            "has_docstring": ast.get_docstring(node) is not None
        }

def generate_baseline_docstring(item: Dict, is_class: bool = False) -> str:
    # ---------- Title ----------
    if is_class:
        title = f"Class: {item['name']}"
    elif item.get("parent_class"):
        title = f"Method: {item['parent_class']}.{item['name']}"
    else:
        title = f"Function: {item['name']}"

    docstring = f'''"""
{title}

'''
    # ---------- Class variables ----------
    if is_class:
        class_vars = item.get("class_variables", [])
        if class_vars:
            docstring += "Class Variables:\n"
            for var in class_vars:
                docstring += f"    {var}\n"
            docstring += "\n"

    # ---------- Parameters ----------
    if not is_class:
        docstring += "Parameters:\n"
        params = item.get("params", [])
        if params:
            for param in params:
                docstring += f"    {param} : description\n"
        else:
            docstring += "    None\n"

        # ---------- Returns ----------
        docstring += f"""
Returns:
    {item.get("returns", "None")}
"""

        # ---------- Local variables ----------
        local_vars = item.get("variables", [])
        if local_vars:
            docstring += "\nLocal Variables:\n"
            for var in local_vars:
                docstring += f"    {var}\n"

    docstring += '"""'
    return docstring



def analyze_code(source: str) -> Dict:
    tree = ast.parse(source)
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)

    return {
        "classes": analyzer.classes,
        "functions": analyzer.functions
    }

def generate_cover_report(analysis: Dict) -> Dict:
    classes = analysis["classes"]
    functions = analysis["functions"]

    report = {
        "total_classes": len(classes),
        "total_functions": len(functions),
        "classes_with_docstrings": [],
        "classes_without_docstrings": [],
        "functions_with_docstrings": [],
        "functions_without_docstrings": [],
        "methods_with_docstrings": [],
        "methods_without_docstrings": []
    }

    # ---- Classes & their methods ----
    for cls in classes:
        if cls["has_docstring"]:
            report["classes_with_docstrings"].append(cls["name"])
        else:
            report["classes_without_docstrings"].append(cls["name"])

        for method in cls["methods"]:
            if method["has_docstring"]:
                report["methods_with_docstrings"].append(
                    f"{cls['name']}.{method['name']}"
                )
            else:
                report["methods_without_docstrings"].append(
                    f"{cls['name']}.{method['name']}"
                )
    # ---- Standalone functions only ----
    for fn in functions:
        if fn["has_docstring"]:
            report["functions_with_docstrings"].append(fn["name"])
        else:
            report["functions_without_docstrings"].append(fn["name"])

    return report