"""T22 — Import-Linter / Layering meta-tests.

Verifies that business-logic layers (core/, report/, tests/ outside tests/hal/)
do not import hardware-specific packages.  Also checks that no cleartext secrets
appear in Python source files.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent  # workspace/cpe-testautomation/

FORBIDDEN_HW_IMPORTS = frozenset(["pysnmp", "ncclient", "pyserial", "paramiko", "scapy"])

# Pattern for cleartext password assignments (e.g. password = "secret")
# Excludes values that start with "Sim" (simulation test stubs) or are
# template variables like ${...}.
_SECRET_PATTERN = re.compile(r'password\s*=\s*["\'][^${\s]', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_imports(file_path: Path) -> set[str]:
    """Extract all imported top-level module names from a Python file."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def collect_py_files(directory: Path) -> list[Path]:
    """Return all .py files under *directory* recursively."""
    return sorted(directory.rglob("*.py"))


def forbidden_imports_in_dir(directory: Path) -> dict[str, set[str]]:
    """Map filename → set-of-forbidden-imports for every file in *directory*."""
    violations: dict[str, set[str]] = {}
    for py_file in collect_py_files(directory):
        found = get_imports(py_file) & FORBIDDEN_HW_IMPORTS
        if found:
            violations[str(py_file.relative_to(PROJECT_ROOT))] = found
    return violations


# ---------------------------------------------------------------------------
# T22 tests
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_core_no_hw_imports():
    """cpe_ta/core/ must not import hardware-driver packages."""
    core_dir = PROJECT_ROOT / "cpe_ta" / "core"
    violations = forbidden_imports_in_dir(core_dir)
    assert not violations, (
        "Forbidden hardware imports found in cpe_ta/core/:\n"
        + "\n".join(f"  {f}: {imps}" for f, imps in violations.items())
    )


@pytest.mark.headless
def test_report_no_hw_imports():
    """cpe_ta/report/ must not import hardware-driver packages."""
    report_dir = PROJECT_ROOT / "cpe_ta" / "report"
    if not report_dir.exists():
        pytest.skip("cpe_ta/report/ not yet created")
    violations = forbidden_imports_in_dir(report_dir)
    assert not violations, (
        "Forbidden hardware imports found in cpe_ta/report/:\n"
        + "\n".join(f"  {f}: {imps}" for f, imps in violations.items())
    )


@pytest.mark.headless
def test_tests_no_hw_imports_except_hal():
    """tests/ (excluding tests/hal/) must not import hardware-driver packages."""
    tests_dir = PROJECT_ROOT / "tests"
    hal_dir = PROJECT_ROOT / "tests" / "hal"
    violations: dict[str, set[str]] = {}
    for py_file in collect_py_files(tests_dir):
        # Skip files under tests/hal/
        try:
            py_file.relative_to(hal_dir)
            continue  # This file is inside tests/hal/ — allowed
        except ValueError:
            pass  # Not under hal/ — check it
        found = get_imports(py_file) & FORBIDDEN_HW_IMPORTS
        if found:
            violations[str(py_file.relative_to(PROJECT_ROOT))] = found
    assert not violations, (
        "Forbidden hardware imports found in tests/ (outside tests/hal/):\n"
        + "\n".join(f"  {f}: {imps}" for f, imps in violations.items())
    )


@pytest.mark.headless
def test_hal_drivers_may_have_hw_imports():
    """cpe_ta/hal/drivers/ is allowed to contain hardware-driver imports (lazy import pattern)."""
    drivers_dir = PROJECT_ROOT / "cpe_ta" / "hal" / "drivers"
    # This test is a positive assertion: we just verify we can scan the directory
    # without crashing, and we do NOT assert the absence of forbidden imports.
    py_files = collect_py_files(drivers_dir)
    assert len(py_files) >= 1, "Expected at least one driver file in cpe_ta/hal/drivers/"
    # Collect all imports — just verify get_imports works without error
    for py_file in py_files:
        imports = get_imports(py_file)
        assert isinstance(imports, set)


# ---------------------------------------------------------------------------
# Secret-Grep
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_no_cleartext_secrets_in_py_files():
    """No Python source file outside test files should contain cleartext password assignments.

    Exceptions:
    - Test/simulation files with "Sim" prefix values (e.g. password = "SimPass123")
      are allowed because they are test stubs, not real credentials.
    """
    cpe_ta_dir = PROJECT_ROOT / "cpe_ta"
    violations: list[str] = []

    for py_file in collect_py_files(cpe_ta_dir):
        text = py_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = _SECRET_PATTERN.search(line)
            if m:
                # Extract the value after the = sign to check for Sim prefix
                value_match = re.search(r'password\s*=\s*["\']([^"\']+)["\']', line, re.IGNORECASE)
                if value_match:
                    value = value_match.group(1)
                    # Allow SimPass* and similar simulator stubs
                    if value.startswith("Sim") or value.startswith("sim"):
                        continue
                violations.append(
                    f"{py_file.relative_to(PROJECT_ROOT)}:{lineno}: {line.strip()}"
                )

    assert not violations, (
        "Potential cleartext secrets found:\n"
        + "\n".join(f"  {v}" for v in violations)
    )
