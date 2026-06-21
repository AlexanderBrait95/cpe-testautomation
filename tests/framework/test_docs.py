"""T38 — Documentation presence tests.

Checks that required documentation files exist and are non-empty.
All tests are headless.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[2]


@pytest.mark.headless
def test_readme_exists() -> None:
    """README.md must exist and be non-empty."""
    readme = PROJECT_ROOT / "README.md"
    assert readme.exists(), "README.md not found"
    assert readme.stat().st_size > 0, "README.md is empty"


@pytest.mark.headless
def test_docs_architecture() -> None:
    """docs/architecture.md must exist."""
    assert (PROJECT_ROOT / "docs" / "architecture.md").exists()


@pytest.mark.headless
def test_docs_testbed() -> None:
    """docs/testbed.md must exist."""
    assert (PROJECT_ROOT / "docs" / "testbed.md").exists()


@pytest.mark.headless
def test_docs_writing_tests() -> None:
    """docs/writing-tests.md must exist."""
    assert (PROJECT_ROOT / "docs" / "writing-tests.md").exists()


@pytest.mark.headless
def test_docs_criteria() -> None:
    """docs/criteria.md must exist."""
    assert (PROJECT_ROOT / "docs" / "criteria.md").exists()


@pytest.mark.headless
def test_docs_deferred_matrix() -> None:
    """docs/deferred-matrix.md must exist."""
    assert (PROJECT_ROOT / "docs" / "deferred-matrix.md").exists()
