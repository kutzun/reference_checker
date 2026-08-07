"""
Tests for author similarity.
"""

from verification.authors import (
    author_similarity,
)


def test_same_authors():

    score = author_similarity(
        [
            "Smith, John",
        ],
        [
            "Smith, John",
        ],
    )

    assert score == 1.0


def test_partial_author_match():

    score = author_similarity(
        [
            "Smith, John",
            "Brown, Alice",
        ],
        [
            "Smith, John",
        ],
    )

    assert score == 0.5
