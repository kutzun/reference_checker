"""
Reference metadata extraction.

Extracts reliable metadata fields from raw reference strings.
"""

import re

from models import Reference
from models.enums import ReferenceType

from .patterns import (
    find_doi,
    find_url,
    find_year,
)
from .text_metadata import (
    extract_authors,
    extract_issue,
    extract_journal,
    extract_pages,
    extract_publisher,
    extract_title,
    extract_volume,
)


def extract_metadata(
    reference: Reference,
) -> Reference:
    """
    Extract metadata from a Reference object.

    Updates the object in place and returns it.

    Args:
        reference:
            Reference containing raw text.

    Returns:
        Updated Reference object.
    """

    # Collapse whitespace runs (PDF/Word hard-wraps) into single spaces
    # for parsing. raw_text is untouched; only this working copy changes.
    text = " ".join(reference.raw_text.split())

    # find_year returns a string so suffixes like "2019b" are preserved.
    # Split back into int year + optional single-letter suffix, so
    # Reference.year keeps its declared int type.
    year_value = find_year(text)
    if year_value is None:
        reference.year = None
        reference.year_suffix = None
    elif year_value[-1:].isalpha():
        reference.year = int(year_value[:-1])
        reference.year_suffix = year_value[-1].lower()
    else:
        reference.year = int(year_value)
        reference.year_suffix = None

    reference.doi = find_doi(text)

    reference.url = find_url(text)

    reference.authors = extract_authors(text)

    reference.title = extract_title(text)

    reference.journal = extract_journal(text)

    reference.volume = extract_volume(text)

    reference.issue = extract_issue(text)

    reference.pages = extract_pages(text)

    reference.publisher = extract_publisher(text)

    reference.reference_type = detect_type(reference, text)

    return reference


def detect_type(reference: Reference, text: str) -> ReferenceType:
    """
    Detect the reference type from a normalized reference string.

    Rules are ordered most-specific first, so a journal article whose
    URL happens to end in .gov.tr/.pdf is not misclassified as a
    government document.

    Args:
        reference:
            Partially populated Reference (journal, publisher, url must
            already be set by the caller).
        text:
            Whitespace-normalized raw reference text.

    Returns:
        ReferenceType, or UNKNOWN if no rule matched.
    """

    # 1. Explicit bracketed markers — unambiguous.
    if re.search(r"\[[^\]]*tez[^\]]*\]", text, re.IGNORECASE):
        return ReferenceType.THESIS
    if re.search(r"\[Video\]", text, re.IGNORECASE):
        return ReferenceType.VIDEO
    if re.search(
        r"\[(?:Conference presentation|Bildiri|Tebliğ|Sunum)\]",
        text,
        re.IGNORECASE,
    ):
        return ReferenceType.CONFERENCE_PROCEEDING

    # 2. Book chapter: "In ... (Eds.)" or "In ... (Cilt N".
    if re.search(r"\bIn\s+.+?\((?:Eds?\.|Cilt\s+\d)", text):
        return ReferenceType.BOOK_CHAPTER

    # 3. Journal article: journal name extracted, or Vol./N(M) markers.
    if reference.journal:
        return ReferenceType.JOURNAL_ARTICLE
    if re.search(r"\bVol\.\s*\d+", text):
        return ReferenceType.JOURNAL_ARTICLE
    if re.search(r",\s*\d+\s*\(\s*\d+\s*\)\s*,", text):
        return ReferenceType.JOURNAL_ARTICLE

    # 4. Turkish conference keywords.
    if re.search(
        r"\b(?:Kongre|Konferans|Sempozyum|Bildiri|Tebliğ)\b",
        text,
        re.IGNORECASE,
    ):
        return ReferenceType.CONFERENCE_PROCEEDING

    # 5. Government document: .gov.tr URL to a PDF.
    if re.search(r"\.gov\.tr", text) and re.search(r"\.pdf\b", text):
        return ReferenceType.GOVERNMENT_DOCUMENT

    # 6. Report: report keywords in the text.
    if re.search(r"\b(?:Report|Outlook|Rapor|Raporu)\b", text):
        return ReferenceType.REPORT

    # 7. Web: has a URL or an access marker.
    if reference.url or re.search(
        r"\b(?:Retrieved|Erişim|Accessed Date)\b", text
    ):
        return ReferenceType.WEB

    # 8. Book: has a publisher or an edition marker.
    if reference.publisher or re.search(
        r"\(\s*\d+\.\s*bask[ıi]\s*\)", text
    ):
        return ReferenceType.BOOK

    return ReferenceType.UNKNOWN