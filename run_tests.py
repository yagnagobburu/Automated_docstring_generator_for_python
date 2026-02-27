"""Clean test runner — shows one summary line per test file."""

import subprocess
import sys


TEST_FILES = {
    "test_syntax_error": "tests/test_syntax_error.py",
    "test_empty_file":   "tests/test_empty_file.py",
    "test_cli_help":     "tests/test_cli_help.py",
}


def run():
    all_passed = True
    print("\n── docgen Test Results ──────────────────────")

    for label, path in TEST_FILES.items():
        result = subprocess.run(
            [sys.executable, "-m", "pytest", path, "-q", "--tb=no", "--no-header"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print(f"  ✅  {label} passed")
        else:
            all_passed = False
            # Extract just the failed count line e.g. "2 failed, 5 passed"
            summary = ""
            for line in result.stdout.splitlines():
                if "failed" in line or "error" in line:
                    summary = line.strip()
                    break
            print(f"  ❌  {label} FAILED  →  {summary}")

    print("─────────────────────────────────────────────")
    if all_passed:
        print("  All tests passed ✅\n")
    else:
        print("  Some tests failed. Run `pytest -v` for details.\n")
        sys.exit(1)


if __name__ == "__main__":
    run()
