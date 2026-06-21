"""JUnit-XML report generator."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from cpe_ta.core.results import RunMetadata, TestResult


def generate_junit_xml(run: RunMetadata, results: list[TestResult]) -> str:
    """Generate JUnit-XML string from run + results."""
    suite = ET.Element("testsuite")
    suite.set("name", run.run_id)
    suite.set("tests", str(run.total_tests))
    suite.set("failures", str(run.failed))
    suite.set("errors", str(run.errors))
    suite.set("skipped", str(run.skipped))
    suite.set("timestamp", str(run.timestamp))

    for r in results:
        tc = ET.SubElement(suite, "testcase")
        tc.set("name", r.test_name)
        tc.set("classname", r.domain)
        tc.set("time", str(r.duration_s))

        if r.outcome == "failed":
            ET.SubElement(tc, "failure").text = str(r.details.get("error", ""))
        elif r.outcome == "error":
            ET.SubElement(tc, "error").text = str(r.details.get("error", ""))
        elif r.outcome == "skipped":
            ET.SubElement(tc, "skipped").text = str(r.details.get("reason", ""))

    raw = ET.tostring(suite, encoding="unicode")
    return minidom.parseString(raw).toprettyxml(indent="  ")


def write_junit_xml(run: RunMetadata, results: list[TestResult], output_path: str) -> None:
    xml_str = generate_junit_xml(run, results)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
