"""
Tests for report generation.
"""

from models import (
    VerificationResult,
    VerificationStatus,
)
from report.generator import (
    ReportGenerator,
)


def test_generate_summary():

    results = [
        VerificationResult(
            status=VerificationStatus.VERIFIED,
            confidence=0.9,
        ),
        VerificationResult(
            status=VerificationStatus.FAILED,
            confidence=0.0,
        ),
    ]

    report = ReportGenerator().generate_summary(results)

    assert report["total"] == 2
    assert report["verified"] == 1
    assert report["failed"] == 1
