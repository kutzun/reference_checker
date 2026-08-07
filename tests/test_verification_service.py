"""
Tests for verification service.
"""

from models import (
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


class MockProvider(VerificationProvider):
    """
    Fake provider for testing.
    """

    @property
    def name(self) -> str:
        return "mock"

    def search(
        self,
        reference: Reference,
    ) -> list[ReferenceMatch]:

        return [
            ReferenceMatch(
                provider=self.name,
            )
        ]


def test_verified_reference():

    reference = Reference(raw_text=("Smith, J. (2020). " "Example article."))

    service = VerificationService(providers=[MockProvider()])

    result = service.verify(reference)

    assert result.status == VerificationStatus.VERIFIED

    assert result.evidence is not None
