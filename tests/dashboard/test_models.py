"""Tests for dashboard Pydantic response models (T-D02)."""
import pytest

from cpe_ta.dashboard.models import (
    DeviceStatus,
    DomainStat,
    LastRun,
    OverviewModel,
    RunDetail,
    RunProgress,
    RunStartRequest,
    RunSummary,
    TestbedStatus,
    TestEntry,
)

pytestmark = pytest.mark.headless


def test_domain_stat_serialisable():
    d = DomainStat(name="lan", passed=10, failed=2, skipped=1, error=0, total=13, pass_rate=0.769)
    out = d.model_dump()
    assert out["name"] == "lan"
    assert out["pass_rate"] == pytest.approx(0.769)


def test_overview_model_empty():
    o = OverviewModel(passed=0, failed=0, skipped=0, error=0, total=0, last_run=None, domains=[])
    j = o.model_dump()
    assert j["last_run"] is None
    assert j["domains"] == []


def test_overview_with_last_run():
    lr = LastRun(run_id="r1", timestamp=1.0, duration_s=30.0, git_sha="abc")
    o = OverviewModel(passed=5, failed=1, skipped=0, error=0, total=6, last_run=lr, domains=[])
    assert o.last_run is not None
    assert o.last_run.run_id == "r1"


def test_run_summary_serialisable():
    r = RunSummary(run_id="r1", timestamp=0.0, duration_s=10.0, passed=3, failed=0, skipped=0, error=0, total=3, git_sha="sha1")
    assert r.model_dump()["run_id"] == "r1"


def test_test_entry_optional_fields():
    e = TestEntry(name="test_foo", domain="lan", status="passed", duration_s=0.1)
    assert e.message is None
    assert e.stacktrace is None


def test_test_entry_failed_with_message():
    e = TestEntry(name="test_bar", domain="wifi", status="failed", duration_s=0.2, message="assertion error")
    assert e.message == "assertion error"


def test_run_detail_serialisable():
    e = TestEntry(name="t", domain="lan", status="passed", duration_s=0.0)
    rd = RunDetail(run_id="r1", timestamp=0.0, duration_s=0.0, git_sha="", tests=[e])
    j = rd.model_dump()
    assert len(j["tests"]) == 1


def test_testbed_status():
    dev = DeviceStatus(name="sw1", type="switch", connected=True)
    tb = TestbedStatus(dut="dut1", hal_devices=[dev], services=["acs"], source="sim")
    j = tb.model_dump()
    assert j["source"] == "sim"
    assert j["hal_devices"][0]["name"] == "sw1"


def test_run_start_request():
    r = RunStartRequest(markers="headless and smoke")
    assert r.markers == "headless and smoke"


def test_run_progress_idle():
    p = RunProgress(status="idle")
    assert p.run_id is None
    assert p.lines_tail == []
    assert p.counts == {}
