"""
Tests for DocxParser footnote extraction.

Footnote text must appear in extract_paragraphs() output so that
citations living only in footnotes are visible to downstream
consumers (internal check, verification).

Fixture: test_data/fixtures/footnote_minimal.docx
  Body paragraph 1: "Body paragraph."
  Body paragraph 2: "A sentence with a footnote marker here."
                    (footnote text: "bkz. Bardakçı (1986).")
  Body paragraph 3: "References"
  Body paragraph 4: "Bardakçı, M. (1986). Title. Publisher."

The token "bkz." appears ONLY in the footnote, never in the body,
so its presence is unambiguous evidence that footnotes were read.
"""

from pathlib import Path

from parser.docx_parser import DocxParser


FIXTURE = (
    Path(__file__).parent.parent
    / "test_data"
    / "fixtures"
    / "footnote_minimal.docx"
)


def test_footnote_text_appears_in_paragraphs():
    """
    On unmodified DocxParser, footnote text is invisible: python-docx's
    document.paragraphs does not read word/footnotes.xml. The result
    is that a citation living only in a footnote is never seen by the
    internal check, and the corresponding reference is falsely
    reported as uncited.

    Asserts on "bkz.", which appears only in the footnote, not in the
    body or reference paragraphs.
    """
    parser = DocxParser(FIXTURE)
    paragraphs = parser.extract_paragraphs()
    joined = "\n".join(paragraphs)

    assert "bkz." in joined, (
        f"footnote text 'bkz.' not found in paragraphs. "
        f"This means word/footnotes.xml was not read. "
        f"Got: {paragraphs!r}"
    )


def test_body_paragraphs_still_extracted():
    """
    Contract guard: the fix must not break normal paragraph extraction.
    The body text must still be present.
    """
    parser = DocxParser(FIXTURE)
    paragraphs = parser.extract_paragraphs()
    joined = "\n".join(paragraphs)

    assert "Body paragraph." in joined
    assert "A sentence with a footnote marker here." in joined