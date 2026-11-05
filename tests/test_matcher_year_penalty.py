"""Regression: year mismatch consumes weight and drags the score down.

Before the 2026-11 fix, ``ReferenceMatcher.score`` treated the year
term as positive-evidence-only: matching years added 0.2 to
``total_weight`` and contributed 1.0, but mismatching years were
silently omitted (no weight added, no penalty). A title-only match
could therefore verify at 1.000 despite a multi-year gap between the
reference year and the candidate year — the exact failure that let
two MEB program entries wrongly verify against the 2005 İlköğretim
program on Google Books.

This file pins the corrected behaviour:

  * year mismatch  → weight 0.2 is added, but contributes 0.0
  * year match     → weight 0.2 is added, contributes 1.0
  * ``evidence_weight`` is identical in both cases
"""

from models import Provider, Reference, ReferenceMatch, ReferenceType
from verification.matcher import ReferenceMatcher


def _make_reference(title: str, year: int) -> Reference:
    return Reference(
        raw_text=f"Smith, J. ({year}). {title}.",
        title=title,
        authors=["Smith, J."],
        year=year,
        reference_type=ReferenceType.JOURNAL_ARTICLE,
    )


def _make_match(title: str, year: int) -> ReferenceMatch:
    return ReferenceMatch(
        provider=Provider.CROSSREF,
        reference_type=ReferenceType.JOURNAL_ARTICLE,
        title=title,
        authors=["Smith, J."],
        year=year,
    )


def test_year_mismatch_drags_perfect_title_author_to_0_8():
    # Title 1.0 (weight 0.5) + author 1.0 (weight 0.3)
    # + year mismatch (weight 0.2, value 0.0)
    # = 0.8 / 1.0 = 0.800 — exactly at VERIFIED_THRESHOLD.
    matcher = ReferenceMatcher()
    ref = _make_reference("A Representative Book Title", year=2024)
    match = _make_match("A Representative Book Title", year=2005)
    score = matcher.score(ref, match)
    assert abs(score - 0.8) < 0.01
    assert match.year_match is False
    assert match.evidence_weight == 1.0


def test_penalty_is_not_gap_dependent():
    # A 1-year gap and a 19-year gap produce the same score —
    # legitimate reprints are a separate concern, not a per-gap
    # discount.
    matcher = ReferenceMatcher()
    ref_2006 = _make_reference("A Representative Book Title", year=2006)
    ref_2024 = _make_reference("A Representative Book Title", year=2024)

    score_1 = matcher.score(
        ref_2006, _make_match("A Representative Book Title", year=2005)
    )
    score_19 = matcher.score(
        ref_2024, _make_match("A Representative Book Title", year=2005)
    )
    assert abs(score_1 - score_19) < 0.01


def test_year_match_keeps_full_score():
    matcher = ReferenceMatcher()
    ref = _make_reference("A Representative Book Title", year=2020)
    match = _make_match("A Representative Book Title", year=2020)
    score = matcher.score(ref, match)
    assert score >= 0.99
    assert match.year_match is True
    assert match.evidence_weight == 1.0


def test_year_mismatch_consumes_weight():
    # Without the fix, evidence_weight would be 0.8 on a mismatch
    # (title 0.5 + author 0.3, year omitted) and 1.0 on a match.
    # With the fix, both cases report 1.0.
    matcher = ReferenceMatcher()
    ref = _make_reference("A Representative Book Title", year=2020)
    mismatched = _make_match("A Representative Book Title", year=2024)
    matched = _make_match("A Representative Book Title", year=2020)

    matcher.score(ref, mismatched)
    matcher.score(ref, matched)
    assert mismatched.evidence_weight == 1.0
    assert matched.evidence_weight == 1.0