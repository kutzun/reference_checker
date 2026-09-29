"""
Tests for OpenLibrary query construction on book-chapter references.

OpenLibrary holds books, not chapters. For a book-chapter reference the
query must be the book title, not the chapter title; otherwise every
chapter lookup returns nothing.
"""

from models import Reference, ReferenceType
from verification.openlibrary_provider import OpenLibraryProvider


class _SpyClient:
    """Capture the query string without making a network call."""
    def __init__(self):
        self.last_query = None

    def search(self, query: str) -> dict:
        self.last_query = query
        return {"docs": []}


def _chapter() -> Reference:
    return Reference(
        raw_text=(
            "Kellogg, R. T. (1996). A model of working memory in writing. "
            "In C. M. Levy & S. Ransdell (Eds.), The science of writing: "
            "Theories, methods, individual differences, and applications "
            "(pp. 57\u201371). Lawrence Erlbaum Associates, Inc."
        ),
        reference_type=ReferenceType.BOOK_CHAPTER,
        authors=["Kellogg, R. T."],
        title="A model of working memory in writing",
        book_title=(
            "The science of writing: Theories, methods, individual "
            "differences, and applications"
        ),
        year=1996,
    )


def _monograph() -> Reference:
    return Reference(
        raw_text="Signell, K. L. (2006). Makam. Yapı Kredi Yayınları.",
        reference_type=ReferenceType.BOOK,
        authors=["Signell, K. L."],
        title="Makam: Türk Sanat Musikisinde Makam Uygulaması",
        year=2006,
    )


def test_chapter_query_uses_book_title():
    spy = _SpyClient()
    provider = OpenLibraryProvider(client=spy)
    provider.search(_chapter())

    assert spy.last_query is not None
    assert "The science of writing" in spy.last_query
    assert "A model of working memory" not in spy.last_query


def test_monograph_query_unchanged():
    """Contract guard: monographs still query their own title."""
    spy = _SpyClient()
    provider = OpenLibraryProvider(client=spy)
    provider.search(_monograph())

    assert spy.last_query is not None
    assert "Makam" in spy.last_query