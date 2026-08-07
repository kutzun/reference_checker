"""
Integration tests for the complete DOCX parsing pipeline.
"""

from pathlib import Path

from docx import Document as DocxDocument

from parser.docx_parser import DocxParser


def create_test_docx(
    path: Path,
    paragraphs: list[str],
) -> None:
    """
    Create a DOCX file for testing.
    """

    document = DocxDocument()

    for paragraph in paragraphs:
        document.add_paragraph(paragraph)

    document.save(path)


def test_parse_references_pipeline(tmp_path):
    file_path = tmp_path / "article.docx"

    create_test_docx(
        file_path,
        [
            "Introduction",
            "Method",
            "Results",
            "References",
            "Smith, J. (2020). Example article.",
            "Jones, A. (2021). Another article.",
            "Appendix",
            "Extra material.",
        ],
    )

    parser = DocxParser(file_path)

    references = parser.parse_references()

    assert len(references) == 2

    assert references[0].raw_text == "Smith, J. (2020). Example article."

    assert references[1].raw_text == "Jones, A. (2021). Another article."
