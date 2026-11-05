"""Regression: institutional author trailing acronyms alias to their
short form so "(MEB, 2024)" resolves against the full-name reference."""

from internal_check.matcher import InternalMatcher
from internal_check.models import (
    CitationKind,
    InTextCitation,
    IssueType,
)
from models import Reference


def _ref(raw: str, author: str, year: int) -> Reference:
    return Reference(raw_text=raw, authors=[author], year=year)


def _cite(raw: str, author: str, year: int) -> InTextCitation:
    return InTextCitation(
        raw=raw,
        kind=CitationKind.PARENTHETICAL,
        authors=[author],
        year=year,
        location="paragraph 1",
        confidence=0.95,
    )


def test_acronym_citation_matches_full_name_reference():
    refs = [_ref(
        "Millî Eğitim Bakanlığı (MEB). (2024). Program.",
        "Millî Eğitim Bakanlığı (MEB)",
        2024,
    )]
    cites = [_cite("(MEB, 2024)", "MEB", 2024)]
    result = InternalMatcher().match(cites, refs)
    assert len(result.issues) == 0


def test_two_meb_years_do_not_cross_match():
    refs = [
        _ref("Millî Eğitim Bakanlığı (MEB). (2006). A.",
             "Millî Eğitim Bakanlığı (MEB)", 2006),
        _ref("Millî Eğitim Bakanlığı (MEB). (2024). B.",
             "Millî Eğitim Bakanlığı (MEB)", 2024),
    ]
    cites = [
        _cite("(MEB, 2006, p. 6)", "MEB", 2006),
        _cite("(MEB, 2024, s. 5)", "MEB", 2024),
    ]
    result = InternalMatcher().match(cites, refs)
    assert len(result.issues) == 0


def test_alias_does_not_mask_uncited():
    """A ref with an alias but no matching citation is still Uncited."""
    refs = [_ref(
        "Millî Eğitim Bakanlığı (MEB). (2020). P.",
        "Millî Eğitim Bakanlığı (MEB)",
        2020,
    )]
    result = InternalMatcher().match([], refs)
    uncited = result.uncited_references()
    assert len(uncited) == 1


def test_alias_does_not_double_count_uncited():
    """One reference with an alias still produces exactly one Uncited
    row, not one per key."""
    refs = [_ref(
        "Millî Eğitim Bakanlığı (MEB). (2020). P.",
        "Millî Eğitim Bakanlığı (MEB)",
        2020,
    )]
    result = InternalMatcher().match([], refs)
    assert len(result.uncited_references()) == 1


def test_mid_parenthetical_not_alias():
    """Only TRAILING parenthetical acronyms are aliased."""
    refs = [_ref(
        "Some (MEB) Thing. (2020). T.",
        "Some (MEB) Thing",
        2020,
    )]
    cites = [_cite("(MEB, 2020)", "MEB", 2020)]
    result = InternalMatcher().match(cites, refs)
    types = [i.issue_type for i in result.issues]
    assert IssueType.MISSING_REFERENCE in types


def test_regular_author_unaffected():
    refs = [_ref("Smith, J. (2020). T.", "Smith, J.", 2020)]
    cites = [_cite("(Smith, 2020)", "Smith", 2020)]
    result = InternalMatcher().match(cites, refs)
    assert len(result.issues) == 0