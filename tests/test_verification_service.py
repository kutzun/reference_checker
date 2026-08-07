"""
Tests for verification service.
"""

from cache.cache import (
    VerificationCache,
)
from models import (
    Provider,
    Reference,
    ReferenceMatch,
    VerificationStatus,
)
from verification.provider import (
    VerificationProvider,
)
from verification.service import (
    VerificationService,
)


class MockProvider(
    VerificationProvider,
):
    """
    Fake provider for testing.
    """

    @property
    def name(
        self,
    ) -> str:
        return "mock"

    def search(
        self,
        reference: Reference,
    ) -> list[ReferenceMatch]:

        return [
            ReferenceMatch(
                provider=Provider.CROSSREF,
                title="Example article",
                authors=["Smith, J."],
                year=2020,
            )
        ]


def test_verified_reference():

    reference = Reference(
        raw_text=("Smith, J. (2020). " "Example article."),
        title="Example article",
        authors=["Smith, J."],
        year=2020,
    )

    service = VerificationService(
        providers=[MockProvider()],
    )

    result = service.verify(reference)

    assert result.status == VerificationStatus.VERIFIED

    assert result.confidence >= 0.80

    assert result.evidence is not None


def test_verified_reference_uses_cache(
    tmp_path,
):

    cache = VerificationCache(tmp_path / "cache.json")

    reference = Reference(
        raw_text=("Smith, J. (2020). " "Example article."),
        title="Example article",
        authors=["Smith, J."],
        year=2020,
    )

    service = VerificationService(
        providers=[MockProvider()],
        cache=cache,
    )

    first_result = service.verify(reference)

    second_result = service.verify(reference)

    assert first_result.status == second_result.status

    assert first_result.confidence == second_result.confidence
