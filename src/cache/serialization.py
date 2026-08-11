"""
Serialization helpers for verification results.
"""

from models import (
    VerificationResult,
)


def result_to_dict(
    result: VerificationResult,
) -> dict:
    """
    Convert VerificationResult to JSON-safe data.
    """

    return {
        "status": result.status.value,
        "confidence": result.confidence,
        "explanation": result.explanation,
        "warnings": result.warnings,
        "search_url": result.search_url,
    }