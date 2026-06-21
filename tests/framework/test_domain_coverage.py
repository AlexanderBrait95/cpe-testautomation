"""T34 — Marker coverage meta-test: verifies all required test domains exist."""
from __future__ import annotations

import pathlib

import pytest

pytestmark = pytest.mark.headless

# Root of the repository (two levels up from this file: tests/framework/ → root)
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent

REQUIRED_DOMAINS: dict[str, str] = {
    "lan": "tests/lan",
    "wifi": "tests/wifi",
    "qos": "tests/qos",
    "wan": "tests/wan",
    "dhcp": "tests/dhcp",
    "multicast": "tests/multicast",
    "ipv6": "tests/ipv6",
    "security": "tests/security",
    "acs": "tests/acs",
    "stress": "tests/stress",
}


@pytest.mark.parametrize("domain,path_str", list(REQUIRED_DOMAINS.items()))
def test_domain_has_test_files(domain: str, path_str: str) -> None:
    """Each required test domain directory must contain at least one test_*.py file."""
    domain_path = _REPO_ROOT / path_str
    assert domain_path.exists(), f"Domain directory missing: {domain_path}"
    assert domain_path.is_dir(), f"Expected a directory: {domain_path}"

    test_files = list(domain_path.glob("test_*.py"))
    assert len(test_files) >= 1, (
        f"Domain '{domain}' has no test_*.py files in {domain_path}"
    )


def test_security_engine_exists() -> None:
    """cpe_ta/core/security.py must exist (security scan engine present)."""
    security_module = _REPO_ROOT / "cpe_ta" / "core" / "security.py"
    assert security_module.exists(), (
        f"Security engine not found: {security_module}"
    )
    assert security_module.is_file()
