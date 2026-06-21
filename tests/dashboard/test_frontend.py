"""Meta-tests for static frontend assets (AC-32, AC-36, AC-40, AC-41, AC-42)."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.headless

_STATIC = Path(__file__).parents[2] / "cpe_ta" / "dashboard" / "static"
_INDEX = _STATIC / "index.html"
_JS = _STATIC / "app.js"


def _index_text() -> str:
    return _INDEX.read_text(encoding="utf-8")


def _js_text() -> str:
    return _JS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-36: 7th nav item + hash route /#/help
# ---------------------------------------------------------------------------

def test_nav_contains_help_link():
    text = _index_text()
    assert "#/help" in text, "index.html must contain a navigation link to #/help"


def test_js_has_help_route():
    text = _js_text()
    assert "/help" in text, "app.js must define a /help route"


def test_js_has_viewHelp_function():
    text = _js_text()
    assert "viewHelp" in text, "app.js must have a viewHelp() function"


def test_js_routes_dict_has_help():
    text = _js_text()
    assert "'/help'" in text or '"/help"' in text, "app.js routes object must map /help"


# ---------------------------------------------------------------------------
# AC-32: Marker presets as controls
# ---------------------------------------------------------------------------

def test_js_has_preset_smoke():
    text = _js_text()
    assert "'smoke'" in text or '"smoke"' in text, "app.js must include 'smoke' preset"


def test_js_has_preset_full():
    text = _js_text()
    assert "'full'" in text or '"full"' in text, "app.js must include 'full' preset"


def test_js_has_preset_regression():
    text = _js_text()
    assert "'regression'" in text or '"regression"' in text, "app.js must include 'regression' preset"


def test_js_has_preset_headless():
    text = _js_text()
    assert "'headless'" in text or '"headless"' in text, "app.js must include 'headless' preset"


def test_js_has_preset_controls_rendering():
    text = _js_text()
    assert "MARKER_PRESETS" in text or "preset" in text.lower(), \
        "app.js must contain marker preset control logic"


# ---------------------------------------------------------------------------
# AC-33: Cancel / abort button
# ---------------------------------------------------------------------------

def test_js_has_cancel_run_function():
    text = _js_text()
    assert "cancelRun" in text or "cancel" in text.lower(), \
        "app.js must have a cancel run function"


def test_js_cancel_calls_cancel_endpoint():
    text = _js_text()
    assert "/runs/active/cancel" in text, \
        "app.js must call /api/runs/active/cancel endpoint"


def test_js_cancel_button_rendered():
    text = _js_text()
    assert "btn-cancel" in text or "Abort" in text or "Cancel" in text or "cancel" in text.lower(), \
        "app.js must render a cancel/abort button during active runs"


# ---------------------------------------------------------------------------
# AC-35: Export links
# ---------------------------------------------------------------------------

def test_js_has_export_links():
    text = _js_text()
    assert "/export" in text, "app.js must reference the /export endpoint"


def test_js_export_has_junit_and_html_formats():
    text = _js_text()
    assert "format=junit" in text or "junit" in text.lower(), \
        "app.js must include junit export format"
    assert "format=html" in text or "html" in text.lower(), \
        "app.js must include html export format"


# ---------------------------------------------------------------------------
# AC-40: Handlungsleitende Leerzustände (empty-state with action)
# ---------------------------------------------------------------------------

def test_js_has_empty_state_function():
    text = _js_text()
    assert "emptyState" in text or "empty-state" in text or "empty_state" in text, \
        "app.js must have an empty-state rendering helper"


def test_js_empty_states_contain_action_links():
    text = _js_text()
    # Action hint must reference either 'Start Run' or 'Help' as next step
    assert "#/start" in text or "#/help" in text, \
        "app.js empty states must contain action links to #/start or #/help"


# ---------------------------------------------------------------------------
# AC-41: Tooltips — ≥5 title= occurrences in index.html + app.js combined
# ---------------------------------------------------------------------------

def test_at_least_5_title_attributes():
    combined = _index_text() + _js_text()
    count = combined.count("title=")
    assert count >= 5, f"Expected ≥5 title= attributes (tooltips), found {count}"


# ---------------------------------------------------------------------------
# AC-42: Central fetch error handler
# ---------------------------------------------------------------------------

def test_js_has_central_fetch_wrapper():
    text = _js_text()
    # The central wrapper must exist and handle non-2xx responses
    assert "apiFetch" in text or "fetch(" in text, \
        "app.js must have a centralized fetch/API wrapper"


def test_js_central_fetch_handles_errors():
    text = _js_text()
    # Must check r.ok or response status
    assert "r.ok" in text or "!r.ok" in text or "response.ok" in text, \
        "app.js fetch wrapper must check response.ok for non-2xx error handling"


def test_js_structured_error_extracted():
    text = _js_text()
    # Must extract 'detail' from the backend error response
    assert "detail" in text, \
        "app.js must extract 'detail' from backend error responses (AC-42)"


# ---------------------------------------------------------------------------
# AC-45: real_status rendered in Help view (TP-03)
# ---------------------------------------------------------------------------

def test_js_renders_real_status():
    text = _js_text()
    assert "real_status" in text, \
        "app.js must reference real_status when rendering hardware/infrastructure entries (AC-45)"


def test_js_real_status_badge_for_skeleton():
    text = _js_text()
    assert "skeleton" in text, \
        "app.js must render a 'skeleton' badge label for skeleton drivers (AC-45)"


def test_offline_invariant_real_status_no_cdn(tmp_path):
    """Adding real_status rendering must not introduce external refs (AC-29 unbroken)."""
    import re as _re
    combined = _index_text() + _js_text()
    external = _re.findall(r'https?://[^\s\'">`]+', combined)
    assert not external, \
        f"External URLs found in static assets (AC-29 violation): {external[:5]}"


# ---------------------------------------------------------------------------
# AC-51: Real-HW onboarding card — no false success claims (TV-01)
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = [
    "tests now target real hardware",
    "the same tests execute against physical hardware",
]


def test_js_no_false_real_hw_success_phrases():
    """AC-51: forbidden success phrases must not appear in app.js."""
    text = _js_text()
    for phrase in _FORBIDDEN_PHRASES:
        assert phrase not in text, (
            f"AC-51 violation: forbidden phrase found in app.js: {phrase!r}"
        )


def test_index_no_false_real_hw_success_phrases():
    """AC-51: forbidden success phrases must not appear in index.html."""
    text = _index_text()
    for phrase in _FORBIDDEN_PHRASES:
        assert phrase not in text, (
            f"AC-51 violation: forbidden phrase found in index.html: {phrase!r}"
        )


def test_js_real_hw_card_has_skeleton_warning():
    """AC-51: 'Switching from Simulator' card must warn that drivers are skeletons."""
    text = _js_text()
    assert "skeleton" in text, \
        "AC-51: app.js must mention 'skeleton' status in the real-HW onboarding card"
    assert "NotImplementedError" in text or "not yet functional" in text or "must be implemented" in text.lower(), \
        "AC-51: app.js must indicate real drivers are not yet functional / must be implemented"


def test_js_real_hw_card_references_architecture_doc():
    """AC-51: the card must reference docs/architecture.md for driver details."""
    text = _js_text()
    assert "architecture.md" in text, \
        "AC-51: app.js must reference docs/architecture.md in the real-HW onboarding card"
