"""HTML report generator using an inline Jinja2 template."""
from __future__ import annotations

from cpe_ta.core.results import RunMetadata, TestResult

_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CPE Test Report — {{ run.run_id }}</title>
<style>
  body { font-family: sans-serif; margin: 2rem; }
  h1 { color: #333; }
  .meta { background: #f4f4f4; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }
  th { background: #e8e8e8; }
  tr.passed td { background: #e6f9e6; }
  tr.failed td { background: #fde8e8; }
  tr.error td { background: #fff3cd; }
  tr.skipped td { background: #f0f0f0; color: #888; }
</style>
</head>
<body>
<h1>CPE Test Report</h1>
<div class="meta">
  <strong>Run ID:</strong> {{ run.run_id }}<br>
  <strong>DUT:</strong> {{ run.dut_id }}<br>
  <strong>Firmware:</strong> {{ run.firmware_version }}<br>
  <strong>Git SHA:</strong> {{ run.git_sha }}<br>
  <strong>Markers:</strong> {{ run.marker_expr or '(none)' }}<br>
  <strong>Total:</strong> {{ run.total_tests }}
  &nbsp; <strong>Passed:</strong> {{ run.passed }}
  &nbsp; <strong>Failed:</strong> {{ run.failed }}
  &nbsp; <strong>Errors:</strong> {{ run.errors }}
  &nbsp; <strong>Skipped:</strong> {{ run.skipped }}
</div>
<table>
  <thead>
    <tr>
      <th>#</th>
      <th>Domain</th>
      <th>Test Name</th>
      <th>Outcome</th>
      <th>Duration (s)</th>
      <th>Details</th>
    </tr>
  </thead>
  <tbody>
  {% for r in results %}
    <tr class="{{ r.outcome }}">
      <td>{{ loop.index }}</td>
      <td>{{ r.domain }}</td>
      <td>{{ r.test_name }}</td>
      <td><strong>{{ r.outcome }}</strong></td>
      <td>{{ "%.3f"|format(r.duration_s) }}</td>
      <td>{{ r.details }}</td>
    </tr>
  {% else %}
    <tr><td colspan="6" style="text-align:center;color:#999;">(no results)</td></tr>
  {% endfor %}
  </tbody>
</table>
</body>
</html>
"""


def generate_html_report(run: RunMetadata, results: list[TestResult]) -> str:
    """Render the HTML report as a string using the inline Jinja2 template."""
    from jinja2 import Environment

    env = Environment(autoescape=True)
    tmpl = env.from_string(_TEMPLATE)
    return tmpl.render(run=run, results=results)


def write_html_report(run: RunMetadata, results: list[TestResult], output_path: str) -> None:
    """Write the HTML report to *output_path*."""
    html = generate_html_report(run, results)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
