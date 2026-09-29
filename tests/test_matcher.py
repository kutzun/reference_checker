"""Tests for the evidence‑weighted scoring logic."""

import pytest
from unittest.mock import patch

from models import Reference, ReferenceMatch, ReferenceType, Provider
from verification.matcher import ReferenceMatcher


@pytest.fixture
def matcher():
    return ReferenceMatcher()


@pytest.fixture
def base_reference():
    return Reference(
        raw_text="Bulté, B., & Housen, A. (2012). Defining ...",
        title="Defining and operationalising L2 complexity",
        authors=["Bulté, B.", "Housen, A."],
        year=2012,
    )


def test_exact_doi_match(matcher, base_reference):
    """
    When DOI matches AND the title is a real match, score is 1.0.
    A DOI alone is not sufficient — see test_matcher_doi_title.py
    for the fabricated-DOI case.
    """
    ref = base_reference
    ref.doi = "10.1075/lllt.32.02bul"
    match = ReferenceMatch(
        provider=Provider.CROSSREF,   # any valid provider
        reference_type=ReferenceType.JOURNAL_ARTICLE,
        title=ref.title,               # title must match for DOI to score
        authors=[],
        year=2012,
        doi="10.1075/lllt.32.02bul",
    )
    score = matcher.score(ref, match)
    assert score == 1.0


def test_title_plus_year_no_authors(matcher, base_reference):
    """Title match + year match, authors missing → score 1.0."""
    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        reference_type=ReferenceType.JOURNAL_ARTICLE,
        title="Defining and operationalising L2 complexity",
        authors=[],              # missing
        year=2012,
    )
    with patch("verification.matcher.token_similarity", return_value=1.0):
        score = matcher.score(base_reference, match)
    assert score == 1.0
    # evidence_weight = title(0.5) + year(0.2) = 0.7
    assert match.evidence_weight == pytest.approx(0.7)


def test_title_only(matcher, base_reference):
    """Only title present – score = title_similarity, evidence_weight = 0.5."""
    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        reference_type=ReferenceType.JOURNAL_ARTICLE,
        title="Defining and operationalising L2 complexity",
        authors=None,
        year=None,
    )
    with patch("verification.matcher.token_similarity", return_value=1.0):
        score = matcher.score(base_reference, match)
    assert score == 1.0
    assert match.evidence_weight == 0.5


def test_title_mismatch_different_year(matcher, base_reference):
    """Title similarity 0.0, year mismatch (ignored) → score 0.0."""
    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        reference_type=ReferenceType.JOURNAL_ARTICLE,
        title="Completely unrelated title",
        authors=[],                     # missing
        year=2020,                      # differs
    )
    with patch("verification.matcher.token_similarity", return_value=0.0):
        score = matcher.score(base_reference, match)
    # title weight 0.5 applied with sim 0.0, year mismatch not counted
    assert score == 0.0
    assert match.evidence_weight == 0.5


def test_partial_author_match(matcher, base_reference):
    """Authors present with partial similarity, title perfect, year perfect."""
    match = ReferenceMatch(
        provider=Provider.CROSSREF,
        reference_type=ReferenceType.JOURNAL_ARTICLE,
        title="Defining and operationalising L2 complexity",
        authors=["Bulté, B."],        # only one author
        year=2012,
    )
    with patch("verification.matcher.token_similarity", return_value=1.0), \
         patch("verification.matcher.author_similarity", return_value=0.5):
        score = matcher.score(base_reference, match)
    # expected = (0.5*1 + 0.3*0.5 + 0.2*1) / (0.5+0.3+0.2) = (0.5+0.15+0.2)/1.0 = 0.85
    assert score == pytest.approx(0.85)
    assert match.evidence_weight == 1.0