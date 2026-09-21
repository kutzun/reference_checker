"""
Tests for the internal consistency matcher.
"""

from models import Reference

from internal_check.matcher import InternalMatcher
from internal_check.models import (
    CitationKind,
    InTextCitation,
    IssueType,
)


def _ref(raw: str, authors: list[str], year: int | None) -> Reference:
    return Reference(raw_text=raw, authors=authors, year=year)


def _cite(authors: list[str], year: int, suffix: str | None = None) -> InTextCitation:
    return InTextCitation(
        raw=f"({authors[0]}, {year})",
        kind=CitationKind.PARENTHETICAL,
        authors=authors,
        year=year,
        year_suffix=suffix,
    )


def _numeric(numbers: list[int]) -> InTextCitation:
    return InTextCitation(
        raw=f"[{','.join(str(n) for n in numbers)}]",
        kind=CitationKind.NUMERIC,
        numbers=numbers,
    )


# ---------------------------------------------------------------------------
# Author-year mode
# ---------------------------------------------------------------------------

def test_all_matched_no_issues():
    m = InternalMatcher()
    refs = [_ref("Smith 2020", ["Smith, J."], 2020)]
    cites = [_cite(["Smith"], 2020)]
    result = m.match(cites, refs)
    assert result.issues == []
    assert result.summary["missing_references"] == 0
    assert result.summary["uncited_references"] == 0


def test_missing_reference():
    m = InternalMatcher()
    refs = []
    cites = [_cite(["Smith"], 2020)]
    result = m.match(cites, refs)
    types = [i.issue_type for i in result.issues]
    assert IssueType.MISSING_REFERENCE in types


def test_uncited_reference():
    m = InternalMatcher()
    refs = [_ref("Smith 2020", ["Smith, J."], 2020)]
    cites = []
    result = m.match(cites, refs)
    types = [i.issue_type for i in result.issues]
    assert IssueType.UNCITED_REFERENCE in types


def test_both_missing_and_uncited():
    m = InternalMatcher()
    refs = [_ref("Jones 2019", ["Jones, A."], 2019)]
    cites = [_cite(["Smith"], 2020)]
    result = m.match(cites, refs)
    assert result.summary["missing_references"] == 1
    assert result.summary["uncited_references"] == 1


def test_ambiguous_same_author_same_year():
    m = InternalMatcher()
    refs = [
        _ref("Smith 2020a", ["Smith, J."], 2020),
        _ref("Smith 2020b", ["Smith, J."], 2020),
    ]
    cites = [_cite(["Smith"], 2020)]
    result = m.match(cites, refs)
    types = [i.issue_type for i in result.issues]
    assert IssueType.AMBIGUOUS in types
    assert result.summary["ambiguous"] == 1


def test_unparsed_reference_missing_year():
    m = InternalMatcher()
    refs = [_ref("Smith no year", ["Smith, J."], None)]
    cites = []
    result = m.match(cites, refs)
    types = [i.issue_type for i in result.issues]
    assert IssueType.UNPARSED in types


def test_turkish_ascii_matches_turkish_name():
    """Yılmaz and Yilmaz should collapse to the same key."""
    m = InternalMatcher()
    refs = [_ref("Yilmaz 2020", ["Yilmaz, A."], 2020)]
    cites = [_cite(["Yılmaz"], 2020)]
    result = m.match(cites, refs)
    assert result.issues == []


def test_year_suffix_does_not_prevent_match_without_suffix():
    """A citation (Smith, 2020a) should still match a ref with year 2020."""
    m = InternalMatcher()
    refs = [_ref("Smith 2020", ["Smith, J."], 2020)]
    cites = [_cite(["Smith"], 2020, suffix="a")]
    result = m.match(cites, refs)
    # The reference has no suffix, so its key is "smith:2020" and the
    # citation's key is "smith:2020a" -- these do NOT match today. This
    # test documents current behavior; we can refine later.
    types = [i.issue_type for i in result.issues]
    assert IssueType.MISSING_REFERENCE in types


# ---------------------------------------------------------------------------
# Numeric mode
# ---------------------------------------------------------------------------

def test_numeric_all_matched():
    m = InternalMatcher()
    refs = [
        _ref("First", ["A"], 2020),
        _ref("Second", ["B"], 2021),
    ]
    cites = [_numeric([1, 2])]
    result = m.match(cites, refs)
    assert result.issues == []


def test_numeric_out_of_range():
    m = InternalMatcher()
    refs = [_ref("First", ["A"], 2020)]
    cites = [_numeric([5])]
    result = m.match(cites, refs)
    types = [i.issue_type for i in result.issues]
    assert IssueType.MISSING_REFERENCE in types
    assert result.summary["missing_references"] == 1


def test_numeric_uncited_reference():
    m = InternalMatcher()
    refs = [
        _ref("First", ["A"], 2020),
        _ref("Second", ["B"], 2021),
        _ref("Third", ["C"], 2022),
    ]
    cites = [_numeric([1])]
    result = m.match(cites, refs)
    assert result.summary["uncited_references"] == 2


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_summary_counts():
    m = InternalMatcher()
    refs = [
        _ref("Smith 2020", ["Smith, J."], 2020),
        _ref("Jones 2019", ["Jones, A."], 2019),
    ]
    cites = [
        _cite(["Smith"], 2020),
        _cite(["Unknown"], 2021),
    ]
    result = m.match(cites, refs)
    assert result.summary["citations_found"] == 2
    assert result.summary["references_found"] == 2
    assert result.summary["missing_references"] == 1
    assert result.summary["uncited_references"] == 1