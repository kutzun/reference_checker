"""
DOCX document parser.

Extracts paragraphs from Word documents and identifies
reference sections.
"""

from pathlib import Path

from docx import Document as DocxDocument

from models import Reference

from .reference_section import (
    find_reference_end,
    find_reference_start,
)
from .reference_splitter import split_references


class DocxParser:
    """
    Parser for Microsoft Word documents.

    Responsible for extracting document text and locating
    reference entries.
    """

    def __init__(self, file_path: Path):
        """
        Initialize parser.

        Args:
            file_path:
                Path to DOCX file.
        """

        self.file_path = file_path

    def extract_paragraphs(self) -> list[str]:
        """
        Extract all non-empty paragraphs from DOCX.

        Returns:
            List of paragraph texts.
        """

        document = DocxDocument(self.file_path)

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return paragraphs

    def extract_reference_section(self) -> list[str]:
        """
        Extract only the reference section content.

        Returns:
            Reference section paragraphs.
        """

        paragraphs = self.extract_paragraphs()

        start_index = find_reference_start(paragraphs)

        if start_index is None:
            return []

        end_index = find_reference_end(
            paragraphs,
            start_index,
        )

        if end_index is None:
            return paragraphs[start_index + 1 :]

        return paragraphs[start_index + 1 : end_index]

    def parse_references(self) -> list[Reference]:
        """
        Convert reference section entries into Reference objects.

        Returns:
            List of Reference instances.
        """

        entries = split_references(self.extract_reference_section())

        return [
            Reference(
                raw_text=entry,
            )
            for entry in entries
        ]
