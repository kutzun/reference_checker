"""
Tests for Google Books query construction on book-chapter references.

A book chapter's author is not the book's author — the book is indexed
under the editors' names, not the chapter writer's. Querying
`intitle:"<chapter title>" inauthor:"<chapter author>"` therefore
returns nothing for a chapter, even when the book is in Google Books.

For BOOK_CHAPTER references the provider must query by book title
alone, with no inauthor filter.
"""

from models import Reference, ReferenceType
from verification.google_books_provider import GoogleBooksProvider


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


def test_chapter_query_uses_book_title_not_chapter_title():
    provider = GoogleBooksProvider(api_key="dummy")
    query = provider._build_query(_chapter())

    assert query is not None
    assert "The science of writing" in query
    assert "A model of working memory" not in query


def test_chapter_query_has_no_inauthor_filter():
    """
    The chapter author is not the book author, so an inauthor filter
    would exclude every correct book from the results.
    """
    provider = GoogleBooksProvider(api_key="dummy")
    query = provider._build_query(_chapter())

    assert query is not None
    assert "inauthor" not in query


def test_monograph_query_unchanged():
    """
    Contract guard: a plain book reference must still query its own
    title with an inauthor filter, exactly as before.
    """
    provider = GoogleBooksProvider(api_key="dummy")
    query = provider._build_query(_monograph())

    assert query is not None
    assert "Makam" in query
    assert "inauthor" in query
    assert "Signell" in query