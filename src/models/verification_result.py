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

    search_url: str | None = None

    # The reference's own URL, if it has one. Copied from Reference.url
    # during verification so the report can display it as a clickable
    # link without needing access to the original Reference object.
    url: str | None = None

    # Link liveness for references that carry a URL. Values match
    # verification.link_checker.LinkStatus ("live", "dead", "unknown"),
    # stored as a plain string to keep models/ free of verification/
    # imports. None means the reference had no URL, or the check was
    # skipped.
    url_status: str | None = None

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