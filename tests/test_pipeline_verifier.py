"""
Tests for manuscript verification pipeline.
"""

from models import (
    Reference,
    VerificationStatus,
)
from pipeline.verifier import (
    ManuscriptVerifier,
)


class FakeVerificationService:
    """
    Fake service for pipeline testing.
    """

    def verify(
        self,
        reference,
    ):

        from models import (
            VerificationResult,
        )

        return VerificationResult(
            status=VerificationStatus.VERIFIED,
            confidence=1.0,
        )


def test_verify_multiple_references():

    verifier = ManuscriptVerifier(FakeVerificationService())

    references = [
        Reference(raw_text="Reference one"),
        Reference(raw_text="Reference two"),
    ]

    results = verifier.verify_references(references)

    assert len(results) == 2

    assert results[0].status == VerificationStatus.VERIFIED
