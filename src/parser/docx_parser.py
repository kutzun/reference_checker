"""
DOCX document parser.

Extracts paragraphs from Word documents and identifies
reference sections.
"""

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from docx import Document as DocxDocument

from extractor.metadata import extract_metadata
from models import Reference

from .reference_section import (
    find_reference_end,
    find_reference_start,
)
from .reference_splitter import split_references


_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


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

        Also extracts footnote texts and appends them as additional
        paragraphs. python-docx does not read word/footnotes.xml, so
        without this, citations living only in footnotes are invisible
        to every downstream consumer of this method.

        Returns:
            List of paragraph texts (body paragraphs followed by
            footnote texts, in that order).
        """

        document = DocxDocument(self.file_path)

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        paragraphs.extend(self._extract_footnote_texts())

        return paragraphs

    def _extract_footnote_texts(self) -> list[str]:
        """
        Read word/footnotes.xml from the DOCX zip and return the text
        content of every real footnote.

        Word stores separator and continuation-separator footnotes with
        ids 0 and -1; those are skipped. Returns an empty list if the
        file has no footnotes or if the archive cannot be read.
        """

        path = Path(self.file_path)
        if not path.exists():
            return []

        try:
            with zipfile.ZipFile(path) as archive:
                if "word/footnotes.xml" not in archive.namelist():
                    return []
                raw_xml = archive.read("word/footnotes.xml")
        except (zipfile.BadZipFile, KeyError, OSError):
            return []

        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError:
            return []

        texts: list[str] = []
        for footnote in root.findall(f".//{{{_W_NS}}}footnote"):
            fn_id = footnote.get(f"{{{_W_NS}}}id")
            if fn_id in ("0", "-1"):
                continue
            parts = [
                (t.text or "")
                for t in footnote.findall(f".//{{{_W_NS}}}t")
            ]
            text = "".join(parts).strip()
            if text:
                texts.append(text)

        return texts

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

        references = [
            Reference(
                raw_text=entry,
            )
            for entry in entries
        ]

        return [extract_metadata(reference) for reference in references]
