"""
Regression tests for Turkish and mixed-style reference extraction.

The fixture file mirrors real end-user input, including paste-joins,
hard-wraps, and typos. Expected values reflect what the parser should
extract from that noisy input, not an idealized form of it.
"""

import pytest

from extractor.metadata import extract_metadata
from internal_check.normalizer import normalize_author_name
from models import Reference

from test_data.turkish_references.books_and_articles import CASES


def _year_key(ref):
    """Reconstruct the year key from int year + optional suffix."""
    if ref.year is None:
        return ""
    return str(ref.year) + (ref.year_suffix or "")


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[c["id"] for c in CASES],
)
def test_turkish_reference_extraction(case):
    case_id = case["id"]
    raw_text = case["raw_text"]
    exp_author = case["first_author"]
    exp_year = case["year"]
    exp_title = case["title"]
    exp_journal = case.get("journal")
    exp_volume = case.get("volume")
    exp_issue = case.get("issue")
    exp_pages = case.get("pages")
    exp_publisher = case.get("publisher")
    exp_type = case["type"]

    ref = extract_metadata(Reference(raw_text=raw_text))

    got_author = normalize_author_name(ref.authors[0]) if ref.authors else ""
    assert got_author == exp_author, (
        f"[{case_id}] author: got {got_author!r}, expected {exp_author!r}"
    )

    got_year = _year_key(ref)
    assert got_year == exp_year, (
        f"[{case_id}] year: got {got_year!r}, expected {exp_year!r}"
    )

    got_title = (ref.title or "").strip()
    assert got_title == exp_title, (
        f"[{case_id}] title: got {got_title!r}, expected {exp_title!r}"
    )

    got_journal = ref.journal or None
    assert got_journal == exp_journal, (
        f"[{case_id}] journal: got {got_journal!r}, expected {exp_journal!r}"
    )

    got_volume = ref.volume or None
    assert got_volume == exp_volume, (
        f"[{case_id}] volume: got {got_volume!r}, expected {exp_volume!r}"
    )

    got_issue = ref.issue or None
    assert got_issue == exp_issue, (
        f"[{case_id}] issue: got {got_issue!r}, expected {exp_issue!r}"
    )

    got_pages = ref.pages or None
    assert got_pages == exp_pages, (
        f"[{case_id}] pages: got {got_pages!r}, expected {exp_pages!r}"
    )

    got_publisher = ref.publisher or None
    assert got_publisher == exp_publisher, (
        f"[{case_id}] publisher: got {got_publisher!r}, expected {exp_publisher!r}"
    )

    got_type = ref.reference_type.value
    assert got_type == exp_type, (
        f"[{case_id}] type: got {got_type!r}, expected {exp_type!r}"
    )