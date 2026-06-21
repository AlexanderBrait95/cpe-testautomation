"""T31 — Security scan tests (headless, smoke)."""
from __future__ import annotations

import pytest

from cpe_ta.core.security import SimSecurityTarget, scan_target

pytestmark = [pytest.mark.headless, pytest.mark.smoke]


def test_scan_clean_target(sim_security_target: SimSecurityTarget) -> None:
    """A default SimSecurityTarget must produce zero security findings."""
    result = scan_target(sim_security_target)
    assert result.findings == [], f"Unexpected findings: {result.findings}"


def test_scan_default_creds(sim_security_target: SimSecurityTarget) -> None:
    """A target with default credentials must produce a default_cred finding."""
    sim_security_target.has_default_creds = True
    result = scan_target(sim_security_target)

    categories = [f.category for f in result.findings]
    assert "default_cred" in categories
    cred_findings = [f for f in result.findings if f.category == "default_cred"]
    assert cred_findings[0].severity == "critical"


def test_scan_telnet_open(sim_security_target: SimSecurityTarget) -> None:
    """A target with port 23 open must produce an open_port finding."""
    sim_security_target.open_ports = [23]
    result = scan_target(sim_security_target)

    categories = [f.category for f in result.findings]
    assert "open_port" in categories


def test_scan_weak_tls(sim_security_target: SimSecurityTarget) -> None:
    """A target with TLS 1.0 must have it listed in weak_tls_versions."""
    sim_security_target.tls_versions = ["TLS 1.0"]
    result = scan_target(sim_security_target)

    assert len(result.weak_tls_versions) > 0
    assert "TLS 1.0" in result.weak_tls_versions


def test_cwmp_tls(sim_security_target: SimSecurityTarget) -> None:
    """Default target uses TLS 1.2/1.3 — these must not appear in weak list."""
    # Default target has TLS 1.2 and TLS 1.3 only
    result = scan_target(sim_security_target)
    assert "TLS 1.2" not in result.weak_tls_versions
    assert "TLS 1.3" not in result.weak_tls_versions
