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
from parser.reference_splitter import (
    split_references,
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

        Runs the reference section through the splitter first, so that
        references spanning multiple paragraphs are joined before
        parsing. Entries without any usable title are dropped.
        """

        parser = DocxParser(file_path)

        paragraphs = parser.extract_reference_section()

        entries = split_references(paragraphs)

        # The splitter already filtered to entries that look like
        # references. The parser extracts whatever metadata it can from
        # each. Entries the parser cannot fully parse are kept — they
        # are still references, and verification will flag them for
        # manual review if no provider can match them.
        return self.reference_parser.parse(entries)