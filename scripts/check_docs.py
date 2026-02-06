import sys
import os
import subprocess
import tomllib

# # 🔧 Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from reports.coverage import calculate_coverage

with open("pyproject.toml", "rb") as f:
    config = tomllib.load(f)

min_coverage = config["tool"]["docstring_tool"]["min_coverage"]

print("Running docstring validation...")

result = subprocess.run(
    ["pydocstyle", "src"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(result.stdout)
    sys.exit(1)

coverage = calculate_coverage("src")
print(f"Docstring coverage: {coverage}%")

if coverage < min_coverage:
    print("Coverage below required threshold")
    sys.exit(1)

print("Documentation checks passed")
