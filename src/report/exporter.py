"""
Report export utilities.

Writes verification reports to common formats.
"""

import csv
import json
from pathlib import Path


class ReportExporter:
    """
    Exports verification reports.
    """

    def export_json(
        self,
        report: dict,
        path: Path,
    ) -> None:
        """
        Export full report (summary + references) as JSON.

        Args:
            report: Detailed report dict from ReportGenerator.generate_detailed_report().
            path: Output file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(report, file, indent=2, ensure_ascii=False)

    def export_csv(
        self,
        report: dict,
        path: Path,
    ) -> None:
        """
        Export report as CSV.

        Writes summary statistics and per‑reference details.

        Args:
            report: Detailed report dict from ReportGenerator.generate_detailed_report().
            path: Output file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Summary section
            writer.writerow(["metric", "value"])
            summary = report.get("summary", {})
            for key, value in summary.items():
                writer.writerow([key, value])

            writer.writerow([])  # blank line

            # References section
            references = report.get("references", [])
            if references:
                writer.writerow(["title", "status", "confidence", "search_url"])
                for ref in references:
                    writer.writerow([
                        ref.get("title", ""),
                        ref.get("status", ""),
                        ref.get("confidence", 0.0),
                        ref.get("search_url", ""),
                    ])