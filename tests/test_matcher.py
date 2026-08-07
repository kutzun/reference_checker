"""
Tests for reference matcher.
"""

from models import (
    Provider,
    Reference,
    ReferenceMatch,
)
from verification.matcher import (
    ReferenceMatcher,
)


def test_doi_exact_match():

    reference = Reference(
        raw_text="Example",
        doi="10.1234/test",
    )

    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        doi="10.1234/test",
    )

    matcher = ReferenceMatcher()

    score = matcher.score(
        reference,
        match,
    )

    assert score == 1.0


def test_title_similarity_match():

    reference = Reference(
        raw_text="Example",
        title="Writing Research",
        year=2020,
    )

    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        title="Writing Research",
        year=2020,
    )

    matcher = ReferenceMatcher()

    score = matcher.score(
        reference,
        match,
    )

    assert score >= 0.7


def test_author_similarity_match():

    reference = Reference(
        raw_text="Example",
        title="Writing Research",
        authors=[
            "Smith, John",
        ],
        year=2020,
    )

    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        title="Writing Research",
        authors=[
            "Smith, John",
        ],
        year=2020,
    )

    matcher = ReferenceMatcher()

    score = matcher.score(
        reference,
        match,
    )

    assert match.author_similarity == 1.0

    assert score == 1.0
