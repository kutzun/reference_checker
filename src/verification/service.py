"""
Verification service.

Coordinates reference verification across providers.
"""

from datetime import datetime
from urllib.parse import quote

from cache.cache import VerificationCache
from cache.serialization import result_to_dict
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
    Coordinates verification across multiple providers.

    Providers are called in order.  If one fails, the service continues
    with the next – it never crashes the whole pipeline.
    """

    def __init__(
        self,
        providers: list[VerificationProvider],
        matcher: ReferenceMatcher | None = None,
        cache: VerificationCache | None = None,
    ) -> None:
        self.providers = providers
        self.matcher = matcher or ReferenceMatcher()
        self.cache = cache

    def verify(self, reference: Reference) -> VerificationResult:
        """
        Verify a single reference against all configured providers.

        Returns a VerificationResult with the best match found.
        """
        # 1. Check cache -------------------------------------------------------
        cache_key = reference.raw_text
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return VerificationResult(
                    status=VerificationStatus(cached["status"]),
                    confidence=cached["confidence"],
                    explanation=cached["explanation"],
                    warnings=cached["warnings"],
                )

        # 2. Query all providers -----------------------------------------------
        evidence = VerificationEvidence(verification_time=datetime.now())
        best_score = 0.0

        for provider in self.providers:
            try:
                matches = provider.search(reference)
            except Exception:
                continue

            if not matches:
                continue

            evidence.add_provider(provider.name)

            for match in matches:
                score = self.matcher.score(reference, match)

                if score > best_score:
                    best_score = score

                evidence.add_match(match)

        # 3. Generate manual search link if not verified -----------------------
        search_url = None
        if best_score < 0.80:
            query = reference.title or reference.raw_text
            if query:
                search_url = f"https://www.google.com/search?q={quote(query)}"

        # 4. Determine final status --------------------------------------------
        if best_score >= 0.80:
            result = VerificationResult(
                status=VerificationStatus.VERIFIED,
                confidence=best_score,
                evidence=evidence,
                explanation="Reference matched with high confidence.",
                search_url=search_url,      # will be None if verified
            )
        elif evidence.matches:
            result = VerificationResult(
                status=VerificationStatus.MANUAL_REVIEW,
                confidence=best_score,
                evidence=evidence,
                explanation="Potential match requires manual review.",
                search_url=search_url,
            )
        else:
            result = VerificationResult(
                status=VerificationStatus.NOT_FOUND,
                confidence=0.0,
                evidence=evidence,
                explanation="No matching reference found.",
                search_url=search_url,
            )

        # 5. Store in cache ----------------------------------------------------
        if self.cache:
            self.cache.set(cache_key, result_to_dict(result))

        return result