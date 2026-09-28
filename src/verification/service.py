"""
Verification service.

Coordinates reference verification across providers using a cascade:
providers are tried in order, and the cascade stops as soon as a
confident match is found. This rations scarce provider quotas (e.g.
Google Books) by spending them only when earlier, typically unlimited,
providers fail to verify a reference.
"""

from datetime import datetime
from urllib.parse import quote

from cache.cache import VerificationCache
from cache.serialization import dict_to_result, result_to_dict
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

    Providers are queried in order. After each provider, if the best
    score so far reaches VERIFIED_THRESHOLD, the cascade stops and no
    further providers are consulted. Provider failures are swallowed —
    a single broken provider never crashes the pipeline.
    """

    # Score at or above which a match is treated as verified and the
    # cascade short-circuits. Anything lower continues to the next
    # provider in the list.
    VERIFIED_THRESHOLD = 0.80

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
        Verify a single reference against configured providers.

        Providers are queried in order until one produces a match at or
        above VERIFIED_THRESHOLD. Returns the best result found.
        """
        # 1. Cache lookup ------------------------------------------------------
        cache_key = reference.raw_text
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return self._restore_from_cache(cached)

        # 2. Cascade through providers ----------------------------------------
        evidence = VerificationEvidence(verification_time=datetime.now())
        best_score = 0.0

        for provider in self.providers:
            # Type-aware routing: providers may declare which reference
            # types they handle. Providers without a `supports` method
            # are always consulted, preserving old behaviour.
            supports = getattr(provider, "supports", None)
            if callable(supports):
                try:
                    if not supports(reference):
                        continue
                except Exception:
                    pass

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

            # Early exit: one confident match is enough. Do not spend
            # downstream provider quota on this reference.
            if best_score >= self.VERIFIED_THRESHOLD:
                break

        # 3. Manual search link (only when below threshold) -------------------
        search_url = None
        if best_score < self.VERIFIED_THRESHOLD:
            title = reference.title or reference.raw_text
            if title:
                search_url = (
                    "https://www.google.com/search?q="
                    f"{quote(f'\"{title}\"')}"
                )

        # 4. Determine final status -------------------------------------------
        if best_score >= self.VERIFIED_THRESHOLD:
            result = VerificationResult(
                status=VerificationStatus.VERIFIED,
                confidence=best_score,
                evidence=evidence,
                explanation="Reference matched with high confidence.",
                search_url=None,
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

        # 5. Cache store ------------------------------------------------------
        if self.cache:
            self.cache.set(cache_key, result_to_dict(result))

        return result

    def _restore_from_cache(self, cached: dict) -> VerificationResult:
        """
        Reconstruct a full VerificationResult from a cached dict.
        """
        return dict_to_result(cached)