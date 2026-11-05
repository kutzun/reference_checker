"""
Tests for book_title extraction from book-chapter references.

APA-style book chapters place the chapter title immediately after the
year, and the book title after "In <editors> (Eds.), ...", terminated
by a "(pp. N–N)" page range. Without extracting book_title, Google
Books and OpenLibrary are queried with the chapter title — which no
book carries — and every chapter goes to manual review.
"""

from extractor.text_metadata import extract_book_title


KELLOGG = (
    "Kellogg, R. T. (1996). A model of working memory in writing. "
    "In C. M. Levy & S. Ransdell (Eds.), The science of writing: "
    "Theories, methods, individual differences, and applications "
    "(pp. 57\u201371). Lawrence Erlbaum Associates, Inc."
)

ROSMAWATI = (
    "Rosmawati, & Lowie, W. (2024). Using a multifractal analysis "
    "approach to explore (multi)fractality in L2 writing in English. "
    "In W. Lowie, Rosmawati, & V. de Wilde (Eds.), Research methods "
    "in complex dynamic systems theory approaches to second language "
    "development (pp. 191\u2013215). John Benjamins."
)


def test_book_title_extracted_apa_single_editor():
    assert extract_book_title(KELLOGG) == (
        "The science of writing: Theories, methods, individual "
        "differences, and applications"
    )


def test_book_title_extracted_apa_multiple_editors():
    assert extract_book_title(ROSMAWATI) == (
        "Research methods in complex dynamic systems theory approaches "
        "to second language development"
    )


def test_book_title_none_for_journal_article():
    """Contract guard: journal articles must not produce a book_title."""
    text = "Smith, J. (2020). Example article. Journal of Examples, 1(1), 1-10."
    assert extract_book_title(text) is None


def test_book_title_none_for_monograph():
    """Contract guard: a plain book reference has no separate book_title."""
    text = (
        "Signell, K. L. (2006). Makam: Türk Sanat Musikisinde Makam "
        "Uygulaması. Yapı Kredi Yayınları."
    )
    assert extract_book_title(text) is None