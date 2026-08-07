"""
Verification report generator.

Creates summaries from verification results.
"""

from models import (
    VerificationResult,
    VerificationStatus,
)


class ReportGenerator:
    """
    Generates verification summaries.
    """

    def generate_summary(
        self,
        results: list[VerificationResult],
    ) -> dict:
        """
        Generate report statistics.

        Args:
            results:
                Verification outcomes.

        Returns:
            Summary dictionary.
        """

        total = len(results)

        verified = sum(
            result.status == VerificationStatus.VERIFIED for result in results
        )

        manual_review = sum(
            result.status == VerificationStatus.MANUAL_REVIEW for result in results
        )

        failed = sum(result.status == VerificationStatus.FAILED for result in results)

        confidence = (
            sum(result.confidence for result in results) / total if total else 0.0
        )

        return {
            "total": total,
            "verified": verified,
            "manual_review": manual_review,
            "failed": failed,
            "average_confidence": confidence,
        }
