import sys
import os
import ast
import tomllib

# 🔧 Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from injector.docstring_injector import DocstringInjector

with open("pyproject.toml", "rb") as f:
    config = tomllib.load(f)

style = config["tool"]["docstring_tool"]["default_style"]

for file in sys.argv[1:]:
    with open(file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    tree = DocstringInjector(style=style).visit(tree)

    with open(file, "w", encoding="utf-8") as f:
        f.write(ast.unparse(tree))

    print(f"Injected docstrings in {file}")

