"""
Tests for matcher scoring of book-chapter references.

Book chapters are unique: the chapter author is not the book author,
and providers return the book (title field = book title). The matcher
must therefore compare reference.book_title against match.title, and
must not compare the chapter author to the book's authors/editors.
Otherwise every correct chapter match scores low and goes to manual
review.
"""

from models import Reference, ReferenceMatch, ReferenceType, Provider
from verification.matcher import ReferenceMatcher


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


def _book_match(title: str, year: int = 1996) -> ReferenceMatch:
    return ReferenceMatch(
        provider=Provider.GOOGLE_BOOKS,
        reference_type=ReferenceType.BOOK,
        record_id="abc",
        title=title,
        authors=["Levy, C. M.", "Ransdell, S."],
        year=year,
        isbn=None,
        publisher=None,
        url=None,
    )


def test_chapter_correct_match_scores_high():
    """
    A correct book match must clear VERIFIED_THRESHOLD (0.80). On
    current code the score is dragged down because the matcher
    compares the chapter title to the book title.
    """
    ref = _chapter()
    match = _book_match(
        "The science of writing: Theories, methods, individual "
        "differences, and applications"
    )

    score = ReferenceMatcher().score(ref, match)
    assert score >= 0.80, (
        f"correct chapter match should verify, got score {score:.3f}"
    )


def test_chapter_wrong_book_scores_low():
    """
    A book with a completely different title must not verify, even
    though the year matches.
    """
    ref = _chapter()
    match = _book_match("Completely unrelated title on a different topic")

    score = ReferenceMatcher().score(ref, match)
    assert score < 0.5, (
        f"wrong book should not verify, got score {score:.3f}"
    )


def test_chapter_author_not_compared_to_book_authors():
    """
    Contract guard: the chapter author (Kellogg) is not the book
    author (Levy, Ransdell). The matcher must not use author similarity
    when scoring a chapter, or every correct match is penalised.
    """
    ref = _chapter()
    match = _book_match(
        "The science of writing: Theories, methods, individual "
        "differences, and applications"
    )

    matcher = ReferenceMatcher()
    matcher.score(ref, match)

    # author_similarity should not have been computed for a chapter
    assert match.author_similarity is None, (
        f"author similarity should be skipped for chapters, "
        f"got {match.author_similarity!r}"
    )


def test_monograph_scoring_unchanged():
    """
    Contract guard: a plain monograph match must still verify as
    before, with title + author + year + publisher.
    """
    ref = Reference(
        raw_text="Signell, K. L. (2006). Makam. Yapı Kredi Yayınları.",
        reference_type=ReferenceType.BOOK,
        authors=["Signell, K. L."],
        title="Makam: Türk Sanat Musikisinde Makam Uygulaması",
        year=2006,
    )
    match = ReferenceMatch(
        provider=Provider.GOOGLE_BOOKS,
        reference_type=ReferenceType.BOOK,
        record_id="xyz",
        title="Makam: Türk Sanat Musikisinde Makam Uygulaması",
        authors=["Signell, Karl L."],
        year=2006,
        isbn=None,
        publisher="Yapı Kredi Yayınları",
        url=None,
    )

    score = ReferenceMatcher().score(ref, match)
    assert score >= 0.80, (
        f"monograph should verify, got score {score:.3f}"
    )