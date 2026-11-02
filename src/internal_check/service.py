"""
Internal-check service.

Ties the extractor and the matcher together. Given a DOCX manuscript,
it splits the body from the reference section, extracts in-text
citations from the body, parses references via the existing pipeline,
and produces an InternalCheckResult.
"""

from pathlib import Path

from models import Reference
from parser.docx_parser import DocxParser
from parser.reference_section import find_reference_start
from workflow.manuscript import ManuscriptProcessor

from .intext_extractor import InTextExtractor
from .matcher import InternalMatcher
from .models import InternalCheckResult
from .profiles import CitationProfile, GENERIC


class InternalCheckService:
    """
    Runs an internal consistency check on a manuscript.
    """

    def __init__(
        self,
        profile: CitationProfile = GENERIC,
        reference_parser=None,
    ) -> None:
        """
        Args:
            profile:
                Citation profile used to interpret in-text citations.
            reference_parser:
                Optional :class:`ReferenceParser` override, forwarded
                to :class:`ManuscriptProcessor`. Mostly useful for
                tests that want to inject a mock parser.
        """
        self.profile = profile
        self.extractor = InTextExtractor(profile)
        self.matcher = InternalMatcher()
        self._processor = ManuscriptProcessor(
            reference_parser=reference_parser,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_docx(self, file_path: Path) -> InternalCheckResult:
        """
        Run the internal check on a DOCX manuscript.

        Args:
            file_path: Path to the DOCX file.

        Returns:
            An :class:`InternalCheckResult` with all issues.
        """
        docx_parser = DocxParser(file_path)
        paragraphs = docx_parser.extract_paragraphs()

        reference_start = find_reference_start(paragraphs)
        if reference_start is None:
            body_paragraphs = paragraphs
        else:
            body_paragraphs = paragraphs[:reference_start]

        references = self._processor.extract_references(file_path)

        citations = self.extractor.extract(body_paragraphs)

        return self.matcher.match(citations, references)

    def check_docx_with_references(
        self,
        file_path: Path,
        references: list[Reference],
    ) -> InternalCheckResult:
        """
        Run the internal check using a caller-supplied reference list.

        Use this when the references have already been reviewed or
        edited elsewhere (e.g. the GUI editor) and should not be
        re-parsed from the DOCX.

        Args:
            file_path: Path to the DOCX file (used only for body text).
            references: Parsed reference-list entries.

        Returns:
            An :class:`InternalCheckResult` with all issues.
        """
        docx_parser = DocxParser(file_path)
        paragraphs = docx_parser.extract_paragraphs()
        reference_start = find_reference_start(paragraphs)
        if reference_start is None:
            body_paragraphs = paragraphs
        else:
            body_paragraphs = paragraphs[:reference_start]

        citations = self.extractor.extract(body_paragraphs)
        return self.matcher.match(citations, references)

    def check_text(
        self,
        body_text: str,
        references: list[Reference],
    ) -> InternalCheckResult:
        """
        Run the internal check on raw body text and pre-parsed references.

        Intended for tests and for callers that already have the body
        text in memory.

        Args:
            body_text: Manuscript body text, reference section excluded.
            references: Parsed reference-list entries.

        Returns:
            An :class:`InternalCheckResult` with all issues.
        """
        citations = self.extractor.extract_text(body_text)
        return self.matcher.match(citations, references)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def unparsed(self) -> list[tuple[str, str]]:
        """
        Segments that the extractor saw but could not classify as
        citations. Each entry is ``(text, location)``.
        """
        return self.extractor.unparsed