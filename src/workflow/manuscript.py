"""
Manuscript processing pipeline.

Extracts references from DOCX files.
"""

from pathlib import Path

from models import (
    Reference,
)
from parser.docx_parser import (
    DocxParser,
)
from parser.reference_parser import (
    ReferenceParser,
)


class ManuscriptProcessor:
    """
    Converts a DOCX manuscript into Reference objects.
    """

    def __init__(
        self,
        reference_parser: ReferenceParser | None = None,
    ):
        """
        Initialize processor.
        """

        self.reference_parser = (
            reference_parser if reference_parser is not None else ReferenceParser()
        )

    def extract_references(
        self,
        file_path: Path,
    ) -> list[Reference]:
        """
        Extract references from DOCX.

        Only returns entries that contain at least a title or a book title.
        This prevents non‑reference text (code, appendix headings, etc.)
        from being passed to the verification pipeline.

        Args:
            file_path:
                Manuscript path.

        Returns:
            Parsed references.
        """

        parser = DocxParser(file_path)

        entries = parser.extract_reference_section()

        all_refs = self.reference_parser.parse(entries)

        # Discard entries without any usable title – they are almost
        # certainly not real bibliographic references.
        filtered = [
            ref for ref in all_refs
            if ref.title or ref.book_title
        ]

        return filtered