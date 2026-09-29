"""
Tests for report exporter.
"""

import csv
import json

from report.exporter import (
    ReportExporter,
)


def test_export_json(
    tmp_path,
):

    path = tmp_path / "report.json"

    report = {
        "total": 10,
        "verified": 8,
    }

    exporter = ReportExporter()

    exporter.export_json(
        report,
        path,
    )

    assert path.exists()

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    assert data == report


def test_export_csv(
    tmp_path,
):

    path = tmp_path / "report.csv"

    report = {
        "total": 10,
        "verified": 8,
    }

    exporter = ReportExporter()

    exporter.export_csv(
        report,
        path,
    )

    assert path.exists()

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        rows = list(csv.reader(file))

    assert rows[0] == [
        "metric",
        "value",
    ]

    assert [
        "total",
        "10",
    ] in rows
