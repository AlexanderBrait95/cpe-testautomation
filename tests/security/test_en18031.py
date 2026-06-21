"""T31 — EN-18031 compliance checklist tests (headless)."""
from __future__ import annotations

import pytest

from cpe_ta.core.security import (
    EN18031_CHECKLIST,
    CheckStatus,
    SimSecurityTarget,
    get_en18031_status,
)

pytestmark = pytest.mark.headless


def test_en18031_items_exist() -> None:
    """The global EN-18031 checklist must contain at least 5 items."""
    assert len(EN18031_CHECKLIST) >= 5


def test_hardcoded_creds_pass() -> None:
    """Clean target → EN18031-1.5.3 (no hardcoded creds) must be PASS."""
    target = SimSecurityTarget()  # has_default_creds=False by default
    items = get_en18031_status(target)
    item = next(i for i in items if i.requirement_id == "EN18031-1.5.3")
    assert item.status == CheckStatus.PASS


def test_hardcoded_creds_fail() -> None:
    """Target with default creds → EN18031-1.5.3 must be FAIL."""
    target = SimSecurityTarget()
    target.has_default_creds = True
    items = get_en18031_status(target)
    item = next(i for i in items if i.requirement_id == "EN18031-1.5.3")
    assert item.status == CheckStatus.FAIL


def test_tls_check_pass() -> None:
    """Target with TLS 1.2/1.3 only → EN18031-1.5.4 must be PASS."""
    target = SimSecurityTarget()  # default: ["TLS 1.2", "TLS 1.3"]
    items = get_en18031_status(target)
    item = next(i for i in items if i.requirement_id == "EN18031-1.5.4")
    assert item.status == CheckStatus.PASS


def test_tls_check_fail() -> None:
    """Target with TLS 1.0 present → EN18031-1.5.4 must be FAIL."""
    target = SimSecurityTarget()
    target.tls_versions = ["TLS 1.0", "TLS 1.2"]
    items = get_en18031_status(target)
    item = next(i for i in items if i.requirement_id == "EN18031-1.5.4")
    assert item.status == CheckStatus.FAIL


def test_manual_items() -> None:
    """All items with automated=False must keep CheckStatus.MANUAL."""
    target = SimSecurityTarget()
    items = get_en18031_status(target)
    for item in items:
        if not item.automated:
            assert item.status == CheckStatus.MANUAL, (
                f"{item.requirement_id} is non-automated but status={item.status}"
            )


def test_evidence_field() -> None:
    """All EN-18031 check items must have an 'evidence' attribute."""
    for item in EN18031_CHECKLIST:
        assert hasattr(item, "evidence"), f"{item.requirement_id} missing evidence field"
