"""
Reference section detection.

Identifies bibliography/reference section boundaries in DOCX documents.
"""

import re

REFERENCE_HEADINGS = {
    "references",
    "reference list",
    "bibliography",
    "works cited",
    "literature cited",
    "literature references",
    "sources",
    "citations",
    "kaynakça",
    "kaynaklar",
    "referanslar",
    "bibliyografi",
    "bibliyografya",
    "literaturverzeichnis",
    "quellenverzeichnis",
    "literaturangaben",
    "literatur",
}


END_SECTION_HEADINGS = {
    "appendix",
    "appendices",
    "supplementary material",
    "supplementary materials",
    "supplemental material",
    "supplemental materials",
    "extended abstract",
    "author biography",
    "author biographies",
    "acknowledgements",
    "acknowledgments",
    "ek",
    "ekler",
    "genişletilmiş özet",
    "teşekkür",
    "anhang",
    "anhänge",
    "zusammenfassung",
    "danksagung",
}


def normalize_heading(text: str) -> str:
    """
    Normalize heading text for comparison.

    Args:
        text:
            Raw paragraph text.

    Returns:
        Normalized heading string.
    """

    text = text.strip().lower()

    text = re.sub(
        r"[:\-–—]+$",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def is_reference_heading(text: str) -> bool:
    """
    Determine whether a paragraph is a reference section heading.

    Args:
        text:
            Paragraph content.

    Returns:
        True if text matches a known reference heading.
    """

    normalized = normalize_heading(text)

    return normalized in REFERENCE_HEADINGS


def is_end_section_heading(text: str) -> bool:
    """
    Determine whether a paragraph marks the end of references.

    Args:
        text:
            Paragraph content.

    Returns:
        True if text matches a known following section.
    """

    normalized = normalize_heading(text)

    return normalized in END_SECTION_HEADINGS


def find_reference_start(paragraphs: list[str]) -> int | None:
    """
    Find the index of the reference section heading.

    Args:
        paragraphs:
            Ordered document paragraphs.

    Returns:
        Index of reference heading, or None if not found.
    """

    for index, paragraph in enumerate(paragraphs):
        if is_reference_heading(paragraph):
            return index

    return None


def find_reference_end(
    paragraphs: list[str],
    start_index: int,
) -> int | None:
    """
    Find the end of the reference section.

    Searches for the first major section heading after references.

    Args:
        paragraphs:
            Ordered document paragraphs.

        start_index:
            Index where references begin.

    Returns:
        Index of the next section heading, or None.
    """

    for index in range(start_index + 1, len(paragraphs)):
        if is_end_section_heading(paragraphs[index]):
            return index

    return None
