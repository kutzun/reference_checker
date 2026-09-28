"""
Tests for DOCX document parsing.
"""

from pathlib import Path

from docx import Document as DocxDocument

from parser.docx_parser import DocxParser


def create_test_docx(
    path: Path,
    paragraphs: list[str],
) -> None:
    """
    Create a temporary DOCX file for testing.
    """

    document = DocxDocument()

    for paragraph in paragraphs:
        document.add_paragraph(paragraph)

    document.save(path)


def test_extract_paragraphs(tmp_path):
    file_path = tmp_path / "test.docx"

    create_test_docx(
        file_path,
        [
            "Introduction",
            "Methods",
            "Results",
        ],
    )

    parser = DocxParser(file_path)

    assert parser.extract_paragraphs() == [
        "Introduction",
        "Methods",
        "Results",
    ]


def test_extract_reference_section(tmp_path):
    file_path = tmp_path / "references.docx"

    create_test_docx(
        file_path,
        [
            "Introduction",
            "Results",
            "References",
            "Smith, J. (2020). Example article.",
            "Jones, A. (2021). Another article.",
        ],
    )

    parser = DocxParser(file_path)

    assert parser.extract_reference_section() == [
        "Smith, J. (2020). Example article.",
        "Jones, A. (2021). Another article.",
    ]


def test_reference_section_stops_at_appendix(tmp_path):
    file_path = tmp_path / "appendix.docx"

    create_test_docx(
        file_path,
        [
            "Introduction",
            "References",
            "Smith, J. (2020). Example article.",
            "Appendix",
            "Additional data table.",
        ],
    )

    parser = DocxParser(file_path)

    assert parser.extract_reference_section() == [
        "Smith, J. (2020). Example article.",
    ]


def test_missing_reference_section(tmp_path):
    file_path = tmp_path / "no_reference.docx"

    create_test_docx(
        file_path,
        [
            "Introduction",
            "Methods",
            "Results",
        ],
    )

    parser = DocxParser(file_path)

    assert parser.extract_reference_section() == []
