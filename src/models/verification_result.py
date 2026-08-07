"""
Verification result data model.

Represents the final outcome of reference verification.
"""

from dataclasses import dataclass, field

from .enums import VerificationStatus
from .verification_evidence import VerificationEvidence


@dataclass
class VerificationResult:
    """
    Final verification outcome for a reference.

    This object combines the decision, confidence, and supporting evidence.
    """

    status: VerificationStatus

    confidence: float = 0.0

    evidence: VerificationEvidence | None = None

    explanation: str = ""

    recommended_action: str = ""

    warnings: list[str] = field(default_factory=list)

    def is_verified(self) -> bool:
        """
        Check whether the reference was successfully verified.

        Returns:
            True if verification status is VERIFIED.
        """
        return self.status == VerificationStatus.VERIFIED

    def requires_review(self) -> bool:
        """
        Check whether manual review is required.

        Returns:
            True if status is MANUAL_REVIEW.
        """
        return self.status == VerificationStatus.MANUAL_REVIEW
