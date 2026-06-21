"""Offline/security meta-test for the dashboard frontend (T-D10, AC-29)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.headless

STATIC_DIR = Path(__file__).parent.parent.parent / "cpe_ta" / "dashboard" / "static"
_EXTERNAL_URL_RE = re.compile(r"https?://[a-zA-Z0-9]")


def test_no_external_urls_in_static():
    """No http:// or https:// to external hosts in any static file (AC-29)."""
    violations: list[str] = []
    for f in STATIC_DIR.rglob("*"):
        if f.is_file() and f.suffix in (".html", ".js", ".css"):
            text = f.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), 1):
                if _EXTERNAL_URL_RE.search(line):
                    violations.append(f"{f.name}:{line_no}: {line.strip()[:80]}")
    assert violations == [], "External URLs found in static files:\n" + "\n".join(violations)


def test_index_html_references_only_local_assets():
    """index.html must link only to app.css and app.js — no CDN."""
    index = STATIC_DIR / "index.html"
    if not index.exists():
        pytest.skip("index.html not found")
    text = index.read_text()
    # Stylesheet
    assert "app.css" in text, "index.html must reference app.css"
    # Script
    assert "app.js" in text, "index.html must reference app.js"
    # No external refs
    assert not _EXTERNAL_URL_RE.search(text), "index.html contains external URL"
