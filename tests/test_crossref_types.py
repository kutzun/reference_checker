"""
Tests for Crossref publication type mapping.
"""

from models import ReferenceType

from verification.crossref_provider import CrossrefProvider


def test_crossref_maps_book():

    item = {
        "type": "book",
    }

    result = CrossrefProvider._reference_type(item)

    assert result == ReferenceType.BOOK


def test_crossref_maps_book_chapter():

    item = {
        "type": "book-chapter",
    }

    result = CrossrefProvider._reference_type(item)

    assert result == ReferenceType.BOOK_CHAPTER


def test_crossref_maps_journal_article():

    item = {
        "type": "journal-article",
    }

    result = CrossrefProvider._reference_type(item)

    assert result == ReferenceType.JOURNAL_ARTICLE


def test_crossref_unknown_type():

    item = {
        "type": "something-new",
    }

    result = CrossrefProvider._reference_type(item)

    assert result == ReferenceType.UNKNOWN