"""
Verification report generator.

Creates summaries and detailed per‑reference reports.
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
        Generate aggregate statistics only.

        Args:
            results: Verification outcomes.

        Returns:
            Summary dictionary (total, verified, manual_review, failed, average_confidence).
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

        not_found = sum(
            result.status == VerificationStatus.NOT_FOUND for result in results
        )

        return {
            "total": total,
            "verified": verified,
            "manual_review": manual_review,
            "failed": failed,
            "not_found": not_found,
            "average_confidence": confidence,
        }

    def generate_detailed_report(
        self,
        results: list[VerificationResult],
    ) -> dict:
        """
        Generate a full report with summary and per‑reference details.

        Args:
            results: Verification outcomes.

        Returns:
            Dictionary with keys 'summary' and 'references'.
        """
        summary = self.generate_summary(results)

        references = []
        for result in results:
            # Best match title if available, else raw reference text
            best_title = None
            if result.evidence and result.evidence.matches:
                best = result.evidence.best_match()
                if best:
                    best_title = best.title

            references.append({
                "title": best_title or "Unknown",
                "status": result.status.value,
                "confidence": result.confidence,
                "search_url": result.search_url,
            })

        return {
            "summary": summary,
            "references": references,
        }