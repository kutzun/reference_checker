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

        Footnote texts are merged into the paragraph that carries the
        footnote marker, so they are visible to the extractor but do
        not become separate paragraphs (which would land inside the
        reference-section span and be misread as bibliography entries).

        Returns:
            List of paragraph texts.
        """

        document = DocxDocument(self.file_path)
        footnote_map = self._build_footnote_map()

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if footnote_map:
                fn_ids = self._footnote_ids_for_paragraph(paragraph)
                fn_texts = [
                    footnote_map[fid]
                    for fid in fn_ids
                    if fid in footnote_map
                ]
                if fn_texts:
                    text = (text + " " + " ".join(fn_texts)).strip()

            if text:
                paragraphs.append(text)

        return paragraphs

    def _footnote_ids_for_paragraph(self, paragraph) -> list[str]:
        """
        Return the w:id values of every footnote reference inside a
        paragraph, in document order.
        """
        ids: list[str] = []
        for elem in paragraph._element.iter():
            tag = elem.tag
            if isinstance(tag, str) and tag.endswith("}footnoteReference"):
                fn_id = elem.get(f"{{{_W_NS}}}id")
                if fn_id:
                    ids.append(fn_id)
        return ids

    def _build_footnote_map(self) -> dict[str, str]:
        """
        Read word/footnotes.xml from the DOCX zip and return a mapping
        from footnote id to footnote text.

        Word stores separator and continuation-separator footnotes with
        ids 0 and -1; those are skipped. Returns an empty dict if the
        file has no footnotes or if the archive cannot be read.
        """

        path = Path(self.file_path)
        if not path.exists():
            return {}

        try:
            with zipfile.ZipFile(path) as archive:
                if "word/footnotes.xml" not in archive.namelist():
                    return {}
                raw_xml = archive.read("word/footnotes.xml")
        except (zipfile.BadZipFile, KeyError, OSError):
            return {}

        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError:
            return {}

        result: dict[str, str] = {}
        for footnote in root.findall(f".//{{{_W_NS}}}footnote"):
            fn_id = footnote.get(f"{{{_W_NS}}}id")
            if fn_id in ("0", "-1") or fn_id is None:
                continue
            parts = [
                (t.text or "")
                for t in footnote.findall(f".//{{{_W_NS}}}t")
            ]
            text = "".join(parts).strip()
            if text:
                result[fn_id] = text

        return result

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
