"""
Tests for GoogleBooksProvider.

GoogleBooksProvider queries the Google Books API and converts returned
Volume resources into ReferenceMatch objects. Tests inject a fake
client, so no HTTP request is made and no API key is required.
"""

import pytest

from models import Reference
from models.enums import Provider, ReferenceType
from verification.google_books_provider import GoogleBooksProvider

from test_data.providers.google_books import (
    EMPTY_RESPONSE,
    INSAN_VE_DEGERLERI,
    MASAL_GUNAY,
)


class FakeGoogleBooksClient:
    """
    Returns a canned API response for any query.
    """

    def __init__(self, response):
        self.response = response
        self.last_query = None

    def search(self, query: str) -> dict:
        self.last_query = query
        return self.response


# ---------------------------------------------------------------------------
# Happy path: full volume conversion
# ---------------------------------------------------------------------------

def test_converts_volume_to_reference_match():
    reference = Reference(
        raw_text="Kuçuradi, İ. (1998). İnsan ve değerleri...",
        title="İnsan ve değerleri",
        authors=["Kuçuradi, İ."],
        year=1998,
    )

    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(INSAN_VE_DEGERLERI),
        api_key="fake-key-for-test",
    )

    matches = provider.search(reference)

    assert len(matches) == 1
    match = matches[0]

    assert match.provider == Provider.GOOGLE_BOOKS
    assert match.reference_type == ReferenceType.BOOK
    assert match.title == "İnsan ve değerleri"
    assert match.authors == ["İoanna Kuçuradi"]
    assert match.publisher == "Türkiye Felsefe Kurumu"
    assert match.year == 1998
    assert match.isbn == "9789757744016"  # ISBN-13 preferred


# ---------------------------------------------------------------------------
# ISBN extraction
# ---------------------------------------------------------------------------

def test_isbn_13_preferred_over_isbn_10():
    reference = Reference(raw_text="test", title="İnsan ve değerleri")

    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(INSAN_VE_DEGERLERI),
        api_key="fake-key-for-test",
    )

    match = provider.search(reference)[0]
    assert match.isbn == "9789757744016"


def test_isbn_10_used_when_no_isbn_13():
    reference = Reference(raw_text="test", title="Masal")

    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(MASAL_GUNAY),
        api_key="fake-key-for-test",
    )

    match = provider.search(reference)[0]
    assert match.isbn == "9754567890"


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

def test_year_extracted_from_iso_date():
    """
    Google Books returns publishedDate as "1998" or "1998-05-01".
    Either form should yield an integer year.
    """
    response = {
        "kind": "books#volumes",
        "totalItems": 1,
        "items": [
            {
                "id": "x",
                "volumeInfo": {
                    "title": "Test Book",
                    "publishedDate": "2014-03-15",
                },
            }
        ],
    }

    reference = Reference(raw_text="test", title="Test Book")
    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(response),
        api_key="fake-key-for-test",
    )

    match = provider.search(reference)[0]
    assert match.year == 2014


# ---------------------------------------------------------------------------
# Empty / missing results
# ---------------------------------------------------------------------------

def test_empty_response_returns_no_matches():
    reference = Reference(raw_text="nothing here", title="Unknown Book")

    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(EMPTY_RESPONSE),
        api_key="fake-key-for-test",
    )

    assert provider.search(reference) == []


def test_missing_items_key_returns_no_matches():
    reference = Reference(raw_text="nothing here", title="Unknown Book")

    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient({"kind": "books#volumes"}),
        api_key="fake-key-for-test",
    )

    assert provider.search(reference) == []


# ---------------------------------------------------------------------------
# Key gating
# ---------------------------------------------------------------------------

def test_supports_false_without_key():
    """
    Without an API key, Google Books returns 429 with quota 0.
    The provider should declare it does not support the reference,
    so the cascade skips it entirely.
    """
    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(INSAN_VE_DEGERLERI),
        api_key=None,
    )

    reference = Reference(raw_text="test", title="İnsan ve değerleri")
    assert provider.supports(reference) is False


def test_supports_true_with_key():
    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(INSAN_VE_DEGERLERI),
        api_key="fake-key-for-test",
    )

    reference = Reference(raw_text="test", title="İnsan ve değerleri")
    assert provider.supports(reference) is True


def test_search_returns_empty_without_key():
    """
    Even if search is called directly (bypassing the service's
    supports() check), no key means no query.
    """
    provider = GoogleBooksProvider(
        client=FakeGoogleBooksClient(INSAN_VE_DEGERLERI),
        api_key=None,
    )

    reference = Reference(raw_text="test", title="İnsan ve değerleri")
    assert provider.search(reference) == []


# ---------------------------------------------------------------------------
# Query construction
# ---------------------------------------------------------------------------

def test_query_includes_title_and_author():
    reference = Reference(
        raw_text="test",
        title="İnsan ve değerleri",
        authors=["Kuçuradi, İ."],
    )

    fake_client = FakeGoogleBooksClient(INSAN_VE_DEGERLERI)
    provider = GoogleBooksProvider(
        client=fake_client,
        api_key="fake-key-for-test",
    )

    provider.search(reference)

    assert fake_client.last_query is not None
    assert "intitle:" in fake_client.last_query
    assert "inauthor:" in fake_client.last_query