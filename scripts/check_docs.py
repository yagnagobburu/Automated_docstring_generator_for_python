# import sys
# import os
# import subprocess
# import tomllib

# # # 🔧 Ensure project root is on PYTHONPATH
# ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.insert(0, ROOT_DIR)

# from reports.coverage import calculate_coverage

# with open("pyproject.toml", "rb") as f:
#     config = tomllib.load(f)

# min_coverage = config["tool"]["docstring_tool"]["min_coverage"]

# print("Running docstring validation...")

# result = subprocess.run(
#     ["pydocstyle", "src"],
#     capture_output=True,
#     text=True
# )

# if result.returncode != 0:
#     print(result.stdout)
#     sys.exit(1)

# coverage = calculate_coverage("src")
# print(f"Docstring coverage: {coverage}%")

# if coverage < min_coverage:
#     print("Coverage below required threshold")
#     sys.exit(1)

# print("Documentation checks passed")
import sys
import os
import subprocess
import tomllib
import tempfile

# 🔧 Ensure project root is on PYTHONPATH
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from reports.coverage import calculate_coverage

# Load config
with open("pyproject.toml", "rb") as f:
    config = tomllib.load(f)

min_coverage = config["tool"]["docstring_tool"]["min_coverage"]

print("Running docstring validation on staged files...")

# 🔹 Get staged Python files
result = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True,
    text=True
)

files = [
    f for f in result.stdout.splitlines()
    if f.startswith("src/") and f.endswith(".py")
]

if not files:
    print("No Python files staged for validation.")
    sys.exit(0)

had_errors = False

# 🔹 Validate docstrings on STAGED content
for file in files:
    staged = subprocess.run(
        ["git", "show", f":{file}"],
        capture_output=True,
        text=True
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(staged.stdout)
        tmp_path = tmp.name

    check = subprocess.run(
        ["pydocstyle", tmp_path],
        capture_output=True,
        text=True
    )

    os.unlink(tmp_path)

    if check.returncode != 0:
        print(f"\nDocstring violations in {file}:")
        print(check.stdout)
        had_errors = True

# 🔴 If violations exist → FAIL FIRST COMMIT
if had_errors:
    sys.exit(1)

# 🔹 Coverage check (only after docstrings pass)
coverage = calculate_coverage("src")
print(f"Docstring coverage: {coverage}%")

if coverage < min_coverage:
    print("Coverage below required threshold")
    sys.exit(1)

print("Documentation checks passed")
sys.exit(0)
