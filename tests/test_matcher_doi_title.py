"""
Tests for the DOI short-circuit in ReferenceMatcher.

A DOI that resolves is not by itself proof that the reference is
correct: an AI-fabricated DOI can point at a real paper on an
unrelated topic. The matcher must compare titles before granting
a verified verdict.
"""

from models import Reference, ReferenceMatch
from models.enums import Provider
from verification.matcher import ReferenceMatcher


def test_doi_match_with_wrong_title_scores_zero():
    """
    Same DOI string, completely different title: score must be 0.0.
    This forces the cascade to continue and try a title-based search.
    """
    reference = Reference(
        raw_text="Fake reference with hijacked DOI.",
        title="On the migration patterns of Arctic terns",
        doi="10.1108/JIMA-08-2019-0171",
    )

    match = ReferenceMatch(
        provider=Provider.DOI_ORG,
        title="Can opinion leaders through Instagram influence organic "
              "food purchase behaviour in Saudi Arabia?",
        authors=["Ahlam Ibrahim Al-Harbi"],
        year=2021,
        doi="10.1108/JIMA-08-2019-0171",
    )

    score = ReferenceMatcher().score(reference, match)

    assert score == 0.0
    assert match.doi_match is True
    assert match.title_similarity is not None
    assert match.title_similarity < 0.3


def test_doi_match_with_matching_title_scores_one():
    """
    Correct DOI and matching title: existing behavior preserved.
    """
    reference = Reference(
        raw_text="Al-Harbi, A.I. & Badawi, N.S. (2022)...",
        title="Can opinion leaders through Instagram influence organic "
              "food purchase behaviour in Saudi Arabia?",
        doi="10.1108/JIMA-08-2019-0171",
    )

    match = ReferenceMatch(
        provider=Provider.DOI_ORG,
        title="Can opinion leaders through Instagram influence organic "
              "food purchase behaviour in Saudi Arabia?",
        doi="10.1108/JIMA-08-2019-0171",
    )

    score = ReferenceMatcher().score(reference, match)

    assert score == 1.0
    assert match.doi_match is True
    assert match.title_similarity == 1.0