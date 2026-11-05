"""
Tests for similarity functions.
"""

from verification.similarity import (
    token_similarity,
)


def test_identical_text_similarity():

    score = token_similarity(
        "Example Article",
        "Example Article",
    )

    assert score == 1.0


def test_different_text_similarity():

    score = token_similarity(
        "Example Article",
        "Completely Different",
    )

    assert score < 1.0
