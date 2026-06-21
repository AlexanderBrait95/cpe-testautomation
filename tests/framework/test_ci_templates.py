"""T37 — CI template validation tests.

Checks that .gitlab-ci.yml and Jenkinsfile are present and structurally correct.
All tests are headless — no subprocess or network calls required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[2]


@pytest.mark.headless
def test_gitlab_ci_yaml_valid() -> None:
    """gitlab-ci.yml must exist and be valid YAML."""
    import yaml

    ci_file = PROJECT_ROOT / ".gitlab-ci.yml"
    assert ci_file.exists(), ".gitlab-ci.yml not found"
    content = ci_file.read_text(encoding="utf-8")
    parsed = yaml.safe_load(content)
    assert isinstance(parsed, dict), "Expected a YAML mapping at the top level"


@pytest.mark.headless
def test_gitlab_ci_has_stages() -> None:
    """gitlab-ci.yml must define the required stages."""
    import yaml

    ci_file = PROJECT_ROOT / ".gitlab-ci.yml"
    parsed = yaml.safe_load(ci_file.read_text(encoding="utf-8"))
    stages = parsed.get("stages", [])
    assert "lint" in stages
    assert "typecheck" in stages
    assert "test" in stages


@pytest.mark.headless
def test_gitlab_ci_has_nightly() -> None:
    """gitlab-ci.yml must contain the nightly-regression job."""
    import yaml

    ci_file = PROJECT_ROOT / ".gitlab-ci.yml"
    parsed = yaml.safe_load(ci_file.read_text(encoding="utf-8"))
    assert "nightly-regression" in parsed, "nightly-regression job missing from .gitlab-ci.yml"


@pytest.mark.headless
def test_jenkinsfile_exists() -> None:
    """Jenkinsfile must exist and contain 'pipeline' and 'stages' keywords."""
    jf = PROJECT_ROOT / "Jenkinsfile"
    assert jf.exists(), "Jenkinsfile not found"
    content = jf.read_text(encoding="utf-8")
    assert "pipeline" in content
    assert "stages" in content
