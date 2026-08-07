"""
Verification service.

Coordinates reference verification across providers.
"""

from datetime import datetime

from models import (
    Reference,
    VerificationEvidence,
    VerificationResult,
    VerificationStatus,
)

from .provider import VerificationProvider


class VerificationService:
    """
    Coordinates verification providers.
    """

    def __init__(
        self,
        providers: list[VerificationProvider],
    ):
        """
        Initialize verification service.

        Args:
            providers:
                Available verification providers.
        """

        self.providers = providers

    def verify(
        self,
        reference: Reference,
    ) -> VerificationResult:
        """
        Verify a reference using available providers.

        Args:
            reference:
                Reference to verify.

        Returns:
            Verification result.
        """

        evidence = VerificationEvidence(
            verification_time=datetime.now(),
        )

        for provider in self.providers:
            matches = provider.search(
                reference
            )

            for match in matches:
                evidence.add_match(match)

            if matches:
                evidence.add_provider(
                    provider.name
                )

        if evidence.matches:
            return VerificationResult(
                status=VerificationStatus.VERIFIED,
                confidence=1.0,
                evidence=evidence,
                explanation=(
                    "Reference matched by "
                    "verification provider."
                ),
            )

        return VerificationResult(
            status=VerificationStatus.NOT_FOUND,
            confidence=0.0,
            evidence=evidence,
            explanation=(
                "No matching reference found."
            ),
        )