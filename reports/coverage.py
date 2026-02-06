import ast
import os

def calculate_coverage(path):
    total = 0
    documented = 0

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        total += 1
                        if ast.get_docstring(node):
                            documented += 1

    return int((documented / total) * 100) if total else 100
