"""
Verification service.

Coordinates reference verification across providers.
"""

from datetime import datetime

from cache.cache import (
    VerificationCache,
)
from cache.serialization import (
    result_to_dict,
)
from models import (
    Reference,
    VerificationEvidence,
    VerificationResult,
    VerificationStatus,
)

from .matcher import ReferenceMatcher
from .provider import VerificationProvider


class VerificationService:
    """
    Coordinates verification providers.
    """

    def __init__(
        self,
        providers: list[VerificationProvider],
        matcher: ReferenceMatcher | None = None,
        cache: VerificationCache | None = None,
    ):
        """
        Initialize verification service.
        """

        self.providers = providers

        self.matcher = matcher if matcher is not None else ReferenceMatcher()

        self.cache = cache

    def verify(
        self,
        reference: Reference,
    ) -> VerificationResult:
        """
        Verify a reference.
        """

        cache_key = reference.raw_text

        if self.cache:

            cached = self.cache.get(cache_key)

            if cached:

                return VerificationResult(
                    status=VerificationStatus(cached["status"]),
                    confidence=cached["confidence"],
                    explanation=cached["explanation"],
                    warnings=cached["warnings"],
                )

        evidence = VerificationEvidence(
            verification_time=datetime.now(),
        )

        best_score = 0.0

        for provider in self.providers:

            matches = provider.search(reference)

            if matches:
                evidence.add_provider(provider.name)

            for match in matches:

                score = self.matcher.score(
                    reference,
                    match,
                )

                best_score = max(
                    best_score,
                    score,
                )

                evidence.add_match(match)

        if best_score >= 0.80:

            result = VerificationResult(
                status=VerificationStatus.VERIFIED,
                confidence=best_score,
                evidence=evidence,
                explanation=("Reference matched " "with high confidence."),
            )

        elif evidence.matches:

            result = VerificationResult(
                status=VerificationStatus.MANUAL_REVIEW,
                confidence=best_score,
                evidence=evidence,
                explanation=("Potential match requires " "review."),
            )

        else:

            result = VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                confidence=0.0,
                evidence=evidence,
                explanation=("No matching reference found."),
            )

        if self.cache:

            self.cache.set(
                cache_key,
                result_to_dict(result),
            )

        return result
