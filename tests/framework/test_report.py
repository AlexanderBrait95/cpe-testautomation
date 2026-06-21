"""T21 — Reporting: JUnit-XML, HTML, Charts, PDF (optional)."""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from cpe_ta.core.results import RunMetadata, TestResult
from cpe_ta.report.charts import generate_latency_chart, generate_throughput_chart
from cpe_ta.report.html import generate_html_report, write_html_report
from cpe_ta.report.junit import generate_junit_xml, write_junit_xml
from cpe_ta.report.pdf import generate_pdf_report

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_run(run_id: str = "run-rpt-001") -> RunMetadata:
    return RunMetadata(
        run_id=run_id,
        dut_id="dut-sim",
        firmware_version="2.1.0",
        timestamp=time.time(),
        git_sha="deadbeef",
        marker_expr="headless",
        total_tests=2,
        passed=1,
        failed=1,
        errors=0,
        skipped=0,
    )


def _make_results(run_id: str = "run-rpt-001") -> list[TestResult]:
    return [
        TestResult(
            test_id="t-pass",
            run_id=run_id,
            dut_id="dut-sim",
            firmware_version="2.1.0",
            timestamp=time.time(),
            git_sha="deadbeef",
            domain="lan",
            test_name="test_lan_throughput",
            outcome="passed",
            duration_s=1.23,
            details={"throughput_mbps": 900.0},
        ),
        TestResult(
            test_id="t-fail",
            run_id=run_id,
            dut_id="dut-sim",
            firmware_version="2.1.0",
            timestamp=time.time(),
            git_sha="deadbeef",
            domain="wifi",
            test_name="test_wifi_ssid",
            outcome="failed",
            duration_s=0.42,
            details={"error": "SSID mismatch"},
        ),
    ]


# ---------------------------------------------------------------------------
# JUnit-XML
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_generate_junit_xml_is_valid_xml():
    """generate_junit_xml must produce parseable XML."""
    run = _make_run()
    results = _make_results()
    xml_str = generate_junit_xml(run, results)
    root = ET.fromstring(xml_str)
    assert root.tag == "testsuite"
    assert root.attrib["name"] == run.run_id


@pytest.mark.headless
def test_generate_junit_xml_failure_element():
    """Failed test must have a <failure> child element in JUnit XML."""
    run = _make_run()
    results = _make_results()
    xml_str = generate_junit_xml(run, results)
    root = ET.fromstring(xml_str)
    testcases = root.findall("testcase")
    failed_tc = next(tc for tc in testcases if tc.attrib["name"] == "test_wifi_ssid")
    assert failed_tc.find("failure") is not None


@pytest.mark.headless
def test_write_junit_xml_creates_file(tmp_path):
    """write_junit_xml must create the output file."""
    out = str(tmp_path / "results.xml")
    run = _make_run()
    results = _make_results()
    write_junit_xml(run, results, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


@pytest.mark.headless
def test_write_junit_xml_file_is_parseable(tmp_path):
    """The file written by write_junit_xml must be valid XML."""
    out = str(tmp_path / "results.xml")
    run = _make_run()
    results = _make_results()
    write_junit_xml(run, results, out)
    root = ET.parse(out).getroot()
    assert root.tag == "testsuite"


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_generate_html_report_contains_run_id():
    """generate_html_report must include the run_id in the output."""
    run = _make_run("my-unique-run-id")
    results = _make_results("my-unique-run-id")
    html = generate_html_report(run, results)
    assert "my-unique-run-id" in html


@pytest.mark.headless
def test_generate_html_report_contains_test_names():
    """generate_html_report must include test names from results."""
    run = _make_run()
    results = _make_results()
    html = generate_html_report(run, results)
    assert "test_lan_throughput" in html
    assert "test_wifi_ssid" in html


@pytest.mark.headless
def test_write_html_report_creates_file(tmp_path):
    """write_html_report must create the output file."""
    out = str(tmp_path / "report.html")
    run = _make_run()
    results = _make_results()
    write_html_report(run, results, out)
    assert Path(out).exists()
    content = Path(out).read_text(encoding="utf-8")
    assert run.run_id in content


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_generate_throughput_chart_creates_png(tmp_path):
    """generate_throughput_chart must create a PNG file."""
    out = str(tmp_path / "throughput.png")
    data = [
        {"firmware_version": "1.0.0", "throughput_mbps": 800.0},
        {"firmware_version": "2.0.0", "throughput_mbps": 920.5},
    ]
    generate_throughput_chart(data, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


@pytest.mark.headless
def test_generate_latency_chart_creates_png(tmp_path):
    """generate_latency_chart must create a PNG file."""
    out = str(tmp_path / "latency.png")
    data = [
        {"firmware_version": "1.0.0", "latency_ms": 5.2},
        {"firmware_version": "2.0.0", "latency_ms": 3.8},
    ]
    generate_latency_chart(data, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


@pytest.mark.headless
def test_throughput_chart_single_entry(tmp_path):
    """generate_throughput_chart must work with a single data point."""
    out = str(tmp_path / "throughput_single.png")
    generate_throughput_chart([{"firmware_version": "1.0", "throughput_mbps": 500.0}], out)
    assert Path(out).exists()


@pytest.mark.headless
def test_latency_chart_single_entry(tmp_path):
    """generate_latency_chart must work with a single data point."""
    out = str(tmp_path / "latency_single.png")
    generate_latency_chart([{"firmware_version": "1.0", "latency_ms": 10.0}], out)
    assert Path(out).exists()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------


@pytest.mark.headless
def test_generate_pdf_report_returns_bool(tmp_path):
    """generate_pdf_report must return bool — True or False, never raise."""
    out = str(tmp_path / "report.pdf")
    html = "<html><body><p>Test</p></body></html>"
    result = generate_pdf_report(html, out)
    assert isinstance(result, bool)


@pytest.mark.headless
def test_generate_pdf_report_no_crash(tmp_path):
    """generate_pdf_report must not raise even when WeasyPrint is absent."""
    out = str(tmp_path / "report2.pdf")
    html = generate_html_report(_make_run(), _make_results())
    # We don't assert True/False — only that it doesn't crash
    result = generate_pdf_report(html, out)
    assert result in (True, False)
