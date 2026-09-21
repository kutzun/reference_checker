"""Report export utilities."""

import json
import csv
from pathlib import Path
from datetime import datetime
from jinja2 import Template

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Reference Checker Report</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fb;
            margin: 20px;
            color: #333;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #243f90;
        }
        .summary {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 15px 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 100px;
        }
        .card .number {
            font-size: 2em;
            font-weight: bold;
        }
        .card .label { font-size: 0.9em; color: #666; }
        .verified .number { color: #2e7d32; }
        .manual .number { color: #cb9932; }
        .failed .number { color: #A91101; }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        th {
            background: #243f90;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td { padding: 10px 12px; border-bottom: 1px solid #e0e0e0; }
        tr:nth-child(even) { background: #f2f5fc; }
        .search-link { color: #243f90; text-decoration: none; }
        .search-link:hover { text-decoration: underline; }
        .verified-text { color: #2e7d32; font-weight: bold; }
        .manual-text { color: #cb9932; font-weight: bold; }
        .failed-text { color: #A91101; font-weight: bold; }
        .footer {
            margin-top: 40px;
            text-align: center;
            font-size: 0.8em;
            color: #888;
        }
        .save-btn {
            background-color: #243f90;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-size: 1em;
            cursor: pointer;
            margin-bottom: 15px;
            display: inline-block;
        }
        .save-btn:hover {
            background-color: #1e3578;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 Reference Checker Report</h1>
        <p>Generated on {{ date }}</p>
    </div>

    <div class="summary">
        <div class="card">
            <div class="number" style="color: #243f90;">{{ summary.total }}</div>
            <div class="label">Total References</div>
        </div>
        <div class="card verified">
            <div class="number">{{ summary.verified }}</div>
            <div class="label">Verified</div>
        </div>
        <div class="card manual">
            <div class="number">{{ summary.manual_review }}</div>
            <div class="label">Manual Review</div>
        </div>
        <div class="card failed">
            <div class="number">{{ summary.failed }}</div>
            <div class="label">Failed</div>
        </div>
        <div class="card">
            <div class="number" style="color: #243f90;">{{ "%.3f"|format(summary.average_confidence) }}</div>
            <div class="label">Avg Confidence</div>
        </div>
    </div>

    <table>
        <tr>
            <th>Reference</th>
            {% if references and references[0].source %}
            <th>Source</th>
            {% endif %}
            <th>Status</th>
            <th>Confidence</th>
            <th>Manual Search</th>
        </tr>
        {% for ref in references %}
        <tr>
            <td>
                {% if ref.raw_text %}
                    {{ ref.raw_text }}
                {% else %}
                    {{ ref.title }}
                {% endif %}
            </td>
            {% if ref.source %}
            <td>{{ ref.source }}</td>
            {% endif %}
            <td>
                {% if ref.status == 'verified' %}
                <span class="verified-text">Verified</span>
                {% elif ref.status == 'manual_review' %}
                <span class="manual-text">Manual Review</span>
                {% else %}
                <span class="failed-text">{{ ref.status }}</span>
                {% endif %}
            </td>
            <td>{{ "%.3f"|format(ref.confidence) }}</td>
            <td>
                {% if ref.search_url %}
                <a class="search-link" href="{{ ref.search_url }}" target="_blank">Google Search</a>
                {% else %}
                —
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>

    <div class="footer">
        <button onclick="saveReport()" class="save-btn">💾 Save Report</button>
        Reference Checker v1.0
    </div>

    <script>
        function saveReport() {
            const html = document.documentElement.outerHTML;
            const blob = new Blob([html], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'reference_report.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
"""


class ReportExporter:
    def export_json(self, report: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def export_csv(self, report: dict, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            # Accept two shapes:
            #   1. A full detailed report with a nested "summary" key
            #      (output of ReportGenerator.generate_detailed_report).
            #   2. A flat summary dict (output of ReportGenerator.generate_summary).
            summary = report.get("summary")
            if summary is None:
                summary = {
                    k: v
                    for k, v in report.items()
                    if k != "references"
                }
            for k, v in summary.items():
                writer.writerow([k, v])
            writer.writerow([])
            refs = report.get("references", [])
            if refs:
                headers = ["reference"]
                if any("source" in ref for ref in refs):
                    headers.append("source")
                headers.extend(["status", "confidence", "search_url"])
                writer.writerow(headers)
                for ref in refs:
                    row = [ref.get("raw_text") or ref.get("title", "")]
                    if "source" in ref:
                        row.append(ref.get("source", ""))
                    row.extend([
                        ref.get("status", ""),
                        ref.get("confidence", 0.0),
                        ref.get("search_url", ""),
                    ])
                    writer.writerow(row)

    def export_html(self, report: dict, path: Path) -> None:
        """Generate an elegant HTML report from the verification result."""
        template = Template(HTML_TEMPLATE)
        html = template.render(
            summary=report.get("summary", {}),
            references=report.get("references", []),
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")