"""
Tests for result serialization.
"""

from cache.serialization import (
    result_to_dict,
)
from models import (
    VerificationResult,
    VerificationStatus,
)


def test_result_serialization():

    result = VerificationResult(
        status=VerificationStatus.VERIFIED,
        confidence=0.95,
        explanation="matched",
    )

    data = result_to_dict(result)

    assert data["status"] == "verified"
    assert data["confidence"] == 0.95
