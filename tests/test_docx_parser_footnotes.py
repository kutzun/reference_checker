"""
Tests for DocxParser footnote extraction.

Footnote text must be visible to downstream consumers (internal
check, verification), but must NOT become a separate paragraph —
otherwise it lands inside the reference-section span and is misread
as a bibliography entry.

Fixture: test_data/fixtures/footnote_minimal.docx
  Body paragraph 1: "Body paragraph."
  Body paragraph 2: "A sentence with a footnote marker here."
                    (footnote text: "bkz. Bardakçı (1986).")
  Body paragraph 3: "References"
  Body paragraph 4: "Bardakçı, M. (1986). Title. Publisher."

Expected result: 4 paragraphs. Footnote text is merged into the
paragraph that carries its marker, not appended as a 5th paragraph
and not attached to the reference paragraph.
"""

from pathlib import Path

from parser.docx_parser import DocxParser


FIXTURE = (
    Path(__file__).parent.parent
    / "test_data"
    / "fixtures"
    / "footnote_minimal.docx"
)


def test_footnote_text_merged_into_marker_paragraph():
    parser = DocxParser(FIXTURE)
    paragraphs = parser.extract_paragraphs()

    assert len(paragraphs) == 4, (
        f"expected 4 paragraphs (footnote text merged, not appended), "
        f"got {len(paragraphs)}: {paragraphs!r}"
    )

    marker_paragraphs = [p for p in paragraphs if "footnote marker" in p]
    assert len(marker_paragraphs) == 1
    assert "bkz." in marker_paragraphs[0], (
        f"footnote text not attached to its marker paragraph: "
        f"{marker_paragraphs[0]!r}"
    )

    reference_paragraphs = [p for p in paragraphs if p.startswith("Bardakçı, M.")]
    assert len(reference_paragraphs) == 1
    assert "bkz." not in reference_paragraphs[0], (
        f"footnote text leaked into the reference paragraph: "
        f"{reference_paragraphs[0]!r}"
    )


def test_body_paragraphs_still_extracted():
    parser = DocxParser(FIXTURE)
    paragraphs = parser.extract_paragraphs()
    joined = "\n".join(paragraphs)

    assert "Body paragraph." in joined
    assert "A sentence with a footnote marker here." in joined