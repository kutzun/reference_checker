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
        Export report as JSON.

        Args:
            report:
                Report data.

            path:
                Output file path.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                report,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def export_csv(
        self,
        report: dict,
        path: Path,
    ) -> None:
        """
        Export report as CSV.

        Args:
            report:
                Report data.

            path:
                Output file path.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                [
                    "metric",
                    "value",
                ]
            )

            for key, value in report.items():

                writer.writerow(
                    [
                        key,
                        value,
                    ]
                )
