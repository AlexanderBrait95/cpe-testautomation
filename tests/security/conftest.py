"""Local conftest for security tests — provides sim_security_target fixture."""
from __future__ import annotations

import pytest

from cpe_ta.core.security import SimSecurityTarget


@pytest.fixture
def sim_security_target() -> SimSecurityTarget:
    """Fresh SimSecurityTarget per test (clean default state)."""
    return SimSecurityTarget()
