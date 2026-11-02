"""
Manuscript verification pipeline.

Runs verification across multiple references.
"""

from models import (
    Reference,
    VerificationResult,
)
from verification.service import (
    VerificationService,
)


class ManuscriptVerifier:
    """
    Coordinates verification of a manuscript's references.
    """

    def __init__(
        self,
        verification_service: VerificationService,
    ):
        """
        Initialize manuscript verifier.

        Args:
            verification_service:
                Service used for individual reference checks.
        """

        self.verification_service = verification_service

    def verify_references(
        self,
        references: list[Reference],
    ) -> list[VerificationResult]:
        """
        Verify multiple references.

        Args:
            references:
                References extracted from a manuscript.

        Returns:
            Verification results.
        """

        results = []

        for reference in references:

            result = self.verification_service.verify(reference)

            results.append(result)

        return results
