"""
End-to-end test for book-chapter verification.

Stitches together the four fixes from this sequence:

  1. Parser extracts book_title for APA chapter references.
  2. Parser sets reference_type = BOOK_CHAPTER.
  3. Google Books / OpenLibrary query by book title, no author filter.
  4. Matcher scores the reference's book_title against the candidate's
     title, and skips the author signal for chapters.

The two fixtures are real entries from a real manuscript. Prior to
this sequence, both went to Manual Review because the parser had no
book_title, the provider queried the chapter title with an inauthor
filter built from the chapter author, and the matcher compared the
chapter title to the book title.
"""

from models import Reference, ReferenceMatch, ReferenceType, Provider
from parser.reference_parser import ReferenceParser
from verification.google_books_provider import GoogleBooksProvider
from verification.matcher import ReferenceMatcher


KELLOGG_RAW = (
    "Kellogg, R. T. (1996). A model of working memory in writing. "
    "In C. M. Levy & S. Ransdell (Eds.), The science of writing: "
    "Theories, methods, individual differences, and applications "
    "(pp. 57\u201371). Lawrence Erlbaum Associates, Inc."
)

KELLOGG_BOOK = (
    "The science of writing: Theories, methods, individual "
    "differences, and applications"
)

ROSMAWATI_RAW = (
    "Rosmawati, & Lowie, W. (2024). Using a multifractal analysis "
    "approach to explore (multi)fractality in L2 writing in English. "
    "In W. Lowie, Rosmawati, & V. de Wilde (Eds.), Research methods "
    "in complex dynamic systems theory approaches to second language "
    "development (pp. 191\u2013215). John Benjamins."
)

ROSMAWATI_BOOK = (
    "Research methods in complex dynamic systems theory approaches "
    "to second language development"
)


def _parse(raw: str) -> Reference:
    return ReferenceParser().parse([raw])[0]


def _simulated_book_match(title: str, year: int) -> ReferenceMatch:
    """
    A Google Books response for the correct book: title matches,
    authors are the editors (not the chapter author), no DOI, no ISBN.
    """
    return ReferenceMatch(
        provider=Provider.GOOGLE_BOOKS,
        reference_type=ReferenceType.BOOK,
        record_id="sim",
        title=title,
        authors=["Levy, C. M.", "Ransdell, S."],
        year=year,
        url=None,
    )


def test_kellogg_chapter_parses_with_book_title():
    ref = _parse(KELLOGG_RAW)
    assert ref.reference_type == ReferenceType.BOOK_CHAPTER
    assert ref.title == "A model of working memory in writing"
    assert ref.book_title == KELLOGG_BOOK


def test_kellogg_chapter_query_and_score():
    ref = _parse(KELLOGG_RAW)

    provider = GoogleBooksProvider(api_key="dummy")
    query = provider._build_query(ref)
    assert query is not None
    assert KELLOGG_BOOK.split(":")[0] in query
    assert "inauthor" not in query

    match = _simulated_book_match(KELLOGG_BOOK, 1996)
    score = ReferenceMatcher().score(ref, match)
    assert score >= 0.80, (
        f"Kellogg chapter should verify, got score {score:.3f}"
    )


def test_rosmawati_chapter_parses_with_book_title():
    ref = _parse(ROSMAWATI_RAW)
    assert ref.reference_type == ReferenceType.BOOK_CHAPTER
    assert ref.book_title == ROSMAWATI_BOOK


def test_rosmawati_chapter_query_and_score():
    ref = _parse(ROSMAWATI_RAW)

    provider = GoogleBooksProvider(api_key="dummy")
    query = provider._build_query(ref)
    assert query is not None
    assert "Research methods" in query
    assert "inauthor" not in query

    match = _simulated_book_match(ROSMAWATI_BOOK, 2024)
    score = ReferenceMatcher().score(ref, match)
    assert score >= 0.80, (
        f"Rosmawati chapter should verify, got score {score:.3f}"
    )